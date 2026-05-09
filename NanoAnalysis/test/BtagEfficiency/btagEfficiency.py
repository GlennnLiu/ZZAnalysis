import os
import numpy as np
import correctionlib
import correctionlib.schemav2 as cs
import gzip
import json
import uproot
import awkward as ak
import ROOT
import matplotlib.pyplot as plt
from matplotlib.colors import LogNorm
from matplotlib.lines import Line2D
import mplhep as hep
from array import array

import argparse

hep.style.use("CMS")

parser = argparse.ArgumentParser()
parser.add_argument("-y", "--year", default="2022EE")
parser.add_argument("-l", "--lumi", default=26.7)
parser.add_argument("-i", "--input", default="/eos/user/a/atarabin/STXS_samples/PROD_samplesNano_2022EE_MC_8d4c03f7/")
parser.add_argument("-m", "--hist-mode", choices=["make", "read"], default="make", help="Make histograms from NanoAOD inputs or read them from the saved ROOT file.")
args = parser.parse_args()

class btagEffCalculator():
    def __init__(self, year, lumi, input_dir):
        self.processes = ["ggH125","VBFH125","WplusH125","WminusH125","ZH125","ttH125","ZZTo4l","ggTo2e2mu_Contin_MCFM701","ggTo2e2tau_Contin_MCFM701","ggTo2mu2tau_Contin_MCFM701","ggTo4e_Contin_MCFM701","ggTo4mu_Contin_MCFM701","ggTo4tau_Contin_MCFM701","WWZ","WZZ","ZZZ","TTWW","TTZZ"]

        self.year = year
        self.lumi = float(lumi)
        self.input_dir = input_dir
        self.file_name = "ZZ4lAnalysis.root"
        self.tree = "Events"

        self.branches = ["Jet_pt","Jet_eta","Jet_jetId","Jet_hadronFlavour","overallEventWeight"]
        self.selections = ["bestCandIdx","Flag_JetVetoed"]

        if int(self.year[:4]) < 2024:
            self.tagger = "Jet_btagPNetB"
            wp = "particleNet_wp_values"
        else:
            self.tagger = "Jet_btagUParTAK4B"
            wp = "UParTAK4_wp_values"

        self.pt_edges = [30,40,50,70,100,150,200,300,600]
        self.eta_edges = [0,0.6,1.2,2.1,2.5]

        self.arrays = None

        if self.year == "2022":
            btag_json = "/cvmfs/cms.cern.ch/rsync/cms-nanoAOD/jsonpog-integration/POG/BTV/2022_Summer22/btagging.json.gz"
        elif self.year == "2022EE":
            btag_json = "/cvmfs/cms.cern.ch/rsync/cms-nanoAOD/jsonpog-integration/POG/BTV/2022_Summer22EE/btagging.json.gz"
        elif self.year == "2023":
            btag_json = "/cvmfs/cms.cern.ch/rsync/cms-nanoAOD/jsonpog-integration/POG/BTV/2023_Summer23/btagging.json.gz"
        elif self.year == "2023BPix":
            btag_json = "/cvmfs/cms.cern.ch/rsync/cms-nanoAOD/jsonpog-integration/POG/BTV/2023_Summer23BPix/btagging.json.gz"
        elif self.year == "2024":
            btag_json = "/cvmfs/cms.cern.ch/rsync/cms-nanoAOD/jsonpog-integration/POG/BTV/2024_Summer24/btagging.json.gz"
        else:
            raise ValueError(f"Unsupported year: {self.year}")

        self.WP = correctionlib.CorrectionSet.from_file(btag_json)[wp].evaluate("M")

    @property
    def get_arrays(self):
        all_arrays = []

        for p in self.processes:
            fname = f"{self.input_dir}/{p}/{self.file_name}"
            print("[get_arrays] Processing ",fname)

            with uproot.open(fname) as f:
                tree = f[self.tree]
                sum_weight = ak.sum(f["Runs"].arrays(['genEventSumw'], library="ak")["genEventSumw"])
            arrays = tree.arrays(
                self.branches + self.selections + [self.tagger], 
                cut="(bestCandIdx>=0) & (Flag_JetVetoed==0)", 
                library="ak"
                )
            arrays = ak.without_field(arrays, self.selections)
            arrays["weight"] = self.lumi*1000*arrays["overallEventWeight"]/sum_weight
            arrays = ak.without_field(arrays, "overallEventWeight")

            flat_arrays = {}
            ref = arrays["Jet_pt"]
            for field in arrays.fields:
                arr = arrays[field]

                is_jagged = True
                try:
                    ak.num(arr, axis=1)
                except Exception:
                    is_jagged = False
                if not is_jagged:
                    arr, _ = ak.broadcast_arrays(arr, ref)

                flat_arrays[field] = ak.flatten(arr)

            arrays = ak.zip(flat_arrays)
            mask = (
                (arrays.Jet_pt > self.pt_edges[0])
                & (np.abs(arrays.Jet_eta) < self.eta_edges[-1])
            )
            arrays = arrays[mask]

            all_arrays.append(arrays)
        
        return ak.concatenate(all_arrays, axis=0)
                    
    def make_histograms(self):
        if self.arrays is None:
            self.arrays = self.get_arrays

        pt = np.asarray(self.arrays.Jet_pt)
        pt = np.minimum(pt, np.nextafter(self.pt_edges[-1], -np.inf))
        eta = np.asarray(np.abs(self.arrays.Jet_eta))
        flav = np.asarray(self.arrays.Jet_hadronFlavour)
        weight = np.asarray(self.arrays.weight)
        tagger = np.asarray(self.arrays[self.tagger])

        # define flavor masks
        flavor_masks = {
            "b": flav == 5,
            "c": flav == 4,
            "light": (flav != 5) & (flav != 4)
        }

        # output containers
        h_all = {}
        h_tagged = {}
        h_eff = {}

        for name, mask in flavor_masks.items():

            # all jets
            h_all[name], _, _ = np.histogram2d(
                pt[mask],
                eta[mask],
                bins=[self.pt_edges, self.eta_edges],
                weights=weight[mask]
            )

            # tagged jets
            tagged_mask = mask & (tagger > self.WP)

            h_tagged[name], _, _ = np.histogram2d(
                pt[tagged_mask],
                eta[tagged_mask],
                bins=[self.pt_edges, self.eta_edges],
                weights=weight[tagged_mask]
            )
            h_eff[name] = np.divide(
                h_tagged[name],
                h_all[name],
                out=np.zeros_like(h_tagged[name], dtype=float),
                where=h_all[name] > 0
            )

        return h_all, h_tagged, h_eff

    def read_histograms(self, filename):
        if not os.path.exists(filename):
            raise FileNotFoundError(f"Histogram file not found: {filename}")

        def th2_to_array(hist):
            nx = hist.GetNbinsX()
            ny = hist.GetNbinsY()
            out = np.zeros((nx, ny), dtype=float)
            for ix in range(nx):
                for iy in range(ny):
                    out[ix, iy] = hist.GetBinContent(ix + 1, iy + 1)
            return out

        h_all = {}
        h_tagged = {}
        h_eff = {}

        f = ROOT.TFile.Open(filename)
        if not f or f.IsZombie():
            raise OSError(f"Could not open histogram file: {filename}")

        for flav in ["b", "c", "light"]:
            for suffix, target in [
                ("all", h_all),
                ("tagged", h_tagged),
                ("eff", h_eff),
            ]:
                hname = f"{flav}_{suffix}"
                hist = f.Get(hname)
                if not hist:
                    f.Close()
                    raise KeyError(f"Missing histogram '{hname}' in {filename}")
                target[flav] = th2_to_array(hist)

        f.Close()
        return h_all, h_tagged, h_eff

    def save_to_root(self, h_all, h_tagged, h_eff, filename):
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        f = ROOT.TFile(filename, "RECREATE")

        for flav in h_all.keys():
            for hname, hdata in [
                (f"{flav}_all",    h_all[flav]),
                (f"{flav}_tagged", h_tagged[flav]),
                (f"{flav}_eff",    h_eff[flav]),
            ]:
                nx = len(self.pt_edges) - 1
                ny = len(self.eta_edges) - 1
                h = ROOT.TH2F(hname, hname,
                            nx, array('d', self.pt_edges),
                            ny, array('d', self.eta_edges))
                for ix in range(nx):
                    for iy in range(ny):
                        h.SetBinContent(ix + 1, iy + 1, hdata[ix, iy])
                h.Write()

        f.Close()

    def save_to_correctionlib_json(self, h_eff, filename):

        pt_edges = list(map(float, self.pt_edges))
        eta_edges = list(map(float, self.eta_edges))

        flavors = ["light", "c", "b"]

        flavor_content = []

        for flav in flavors:

            hist = np.nan_to_num(h_eff[flav], nan=0.0)
            pt_content = []

            for i_pt in range(len(pt_edges) - 1):

                eta_content = hist[i_pt].tolist()

                pt_content.append(
                    cs.Binning(
                        nodetype="binning",
                        input="abseta",
                        edges=eta_edges,
                        content=eta_content,
                        flow="clamp",
                    )
                )

            flavor_content.append(
                cs.CategoryItem(
                    key=flav,
                    value=cs.Binning(
                        nodetype="binning",
                        input="pt",
                        edges=pt_edges,
                        content=pt_content,
                        flow="clamp",
                    ),
                )
            )

        # final correction object
        corr = cs.Correction(
            name="btag_efficiency",
            description="CMS Run-3 b-tag efficiency maps for HZZ",
            version=1,
            inputs=[
                cs.Variable(name="flavor", type="string"),
                cs.Variable(name="pt", type="real"),
                cs.Variable(name="abseta", type="real"),
            ],
            output=cs.Variable(name="efficiency", type="real"),
            data=cs.Category(
                nodetype="category",
                input="flavor",
                content=flavor_content,
            ),
        )

        # wrap into correction set
        cset = cs.CorrectionSet(
            schema_version=2,
            description="CMS Run-3 b-tag efficiency maps for HZZ (pt, eta, flavor)",
            corrections=[corr],
        )

        # write compressed JSON
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        with gzip.open(filename, "wt") as f:
            if hasattr(cset, "model_dump_json"):
                f.write(cset.model_dump_json(indent=2, exclude_unset=True))
                f.write("\n")
            else:
                json.dump(cset.dict(exclude_unset=True), f, indent=2)

    def plot_2d_hist(self, hist, name, outname, zmin=None, zmax=None, cmap="viridis"):

        pt_edges = np.array(self.pt_edges)
        eta_edges = np.array(self.eta_edges)

        h = np.array(hist, dtype=float)
        h_plot = np.ma.masked_less_equal(h, 0.0)
        positive = h[h > 0]
        log_vmin = zmin if zmin is not None and zmin > 0 else (positive.min() if positive.size else 1e-6)
        log_vmax = zmax if zmax is not None else (positive.max() if positive.size else 1.0)

        fig, ax = plt.subplots(figsize=(11, 9))

        mesh = ax.pcolormesh(
            pt_edges,
            eta_edges,
            h_plot.T,
            shading="auto",
            norm=LogNorm(vmin=log_vmin, vmax=log_vmax),
            cmap=cmap,
        )

        fig.colorbar(mesh, ax=ax, label=name, pad=0.01)

        ax.set_xlabel(r"$p_T$ [GeV]")
        ax.set_ylabel(r"$|\eta|$")
        hep.cms.label("Preliminary", data=False, lumi=self.lumi, com=13.6, ax=ax)

        os.makedirs(os.path.dirname(outname), exist_ok=True)

        fig.savefig(outname + ".png", bbox_inches="tight")
        fig.savefig(outname + ".pdf", bbox_inches="tight")

        plt.close(fig)

    def plot_1d_hist(self, hist, name, outname, ymin=1e-3, ymax=1.0):

        pt_edges = np.array(self.pt_edges, dtype=float)
        eta_edges = np.array(self.eta_edges, dtype=float)
        h = np.array(hist, dtype=float)

        fig, ax = plt.subplots(figsize=(11, 9))

        for i_eta in range(len(eta_edges) - 1):
            y = np.ma.masked_less_equal(h[:, i_eta], 0.0)
            label = rf"${eta_edges[i_eta]:g} \leq |\eta| < {eta_edges[i_eta + 1]:g}$"
            ax.stairs(y, pt_edges, label=label, linewidth=2.5)

        ax.set_xlabel(r"$p_T$ [GeV]")
        ax.set_ylabel(name)
        ax.set_xlim(pt_edges[0], pt_edges[-1])
        ax.set_ylim(ymin, ymax)
        ax.set_yscale("log")
        ax.legend(loc="best", title=r"$|\eta|$ bins")
        hep.cms.label("Preliminary", data=False, lumi=self.lumi, com=13.6, ax=ax)

        os.makedirs(os.path.dirname(outname), exist_ok=True)

        fig.savefig(outname + ".png", bbox_inches="tight")
        fig.savefig(outname + ".pdf", bbox_inches="tight")

        plt.close(fig)

    def plot_1d_all_flavors(self, h_eff, outname, ymin=1e-3, ymax=1.0):

        pt_edges = np.array(self.pt_edges, dtype=float)
        eta_edges = np.array(self.eta_edges, dtype=float)
        flavors = ["light", "c", "b"]
        line_styles = {
            "light": "-",
            "c": "--",
            "b": ":",
        }
        eta_colors = plt.rcParams["axes.prop_cycle"].by_key()["color"][:len(eta_edges) - 1]

        fig, ax = plt.subplots(figsize=(16, 10))
        fig.subplots_adjust(right=0.70, top=0.82)

        for flav in flavors:
            h = np.array(h_eff[flav], dtype=float)
            for i_eta, color in enumerate(eta_colors):
                y = np.ma.masked_less_equal(h[:, i_eta], 0.0)
                ax.stairs(
                    y,
                    pt_edges,
                    color=color,
                    linestyle=line_styles[flav],
                    linewidth=2.5,
                )

        eta_handles = [
            Line2D(
                [0],
                [0],
                color=eta_colors[i_eta],
                linewidth=2.5,
                label=rf"$[{eta_edges[i_eta]:g}, {eta_edges[i_eta + 1]:g})$",
            )
            for i_eta in range(len(eta_edges) - 1)
        ]
        flavor_handles = [
            Line2D(
                [0],
                [0],
                color="black",
                linestyle=line_styles[flav],
                linewidth=2.5,
                label=flav,
            )
            for flav in flavors
        ]

        eta_legend = ax.legend(
            handles=eta_handles,
            loc="upper left",
            bbox_to_anchor=(1.02, 1.0),
            title=r"$|\eta|$ bins",
            borderaxespad=0.0,
        )
        ax.add_artist(eta_legend)
        flavor_legend = ax.legend(
            handles=flavor_handles,
            loc="upper left",
            bbox_to_anchor=(1.02, 0.48),
            title="Flavor",
            borderaxespad=0.0,
        )

        ax.set_xlabel(r"$p_T$ [GeV]")
        ax.set_ylabel("b-tag efficiency")
        ax.set_xlim(pt_edges[0], pt_edges[-1])
        ax.set_ylim(ymin, ymax)
        ax.set_yscale("log")
        cms_label = hep.cms.label("Preliminary", data=False, lumi=self.lumi, com=13.6, ax=ax)
        extra_artists = [eta_legend, flavor_legend]
        if isinstance(cms_label, (list, tuple)):
            extra_artists.extend(cms_label)
        elif cms_label is not None:
            extra_artists.append(cms_label)

        os.makedirs(os.path.dirname(outname), exist_ok=True)

        fig.savefig(
            outname + ".png",
            bbox_inches="tight",
            bbox_extra_artists=extra_artists,
            pad_inches=0.2,
        )
        fig.savefig(
            outname + ".pdf",
            bbox_inches="tight",
            bbox_extra_artists=extra_artists,
            pad_inches=0.2,
        )

        plt.close(fig)


btag = btagEffCalculator(args.year, args.lumi, args.input)
root_file = f"../../data/btagEff/btag_{args.year}.root"
if args.hist_mode == "make":
    h_all, h_tagged, h_eff = btag.make_histograms()
    btag.save_to_root(h_all, h_tagged, h_eff, root_file)
else:
    h_all, h_tagged, h_eff = btag.read_histograms(root_file)
btag.save_to_correctionlib_json(h_eff, f"../../data/btagEff/btag_{args.year}.json.gz")
for flav in h_eff.keys():
    btag.plot_2d_hist(h_eff[flav], f"b-tag efficiency for {flav} jets", f"../../data/btagEff/plots/btag_eff_{flav}_{args.year}_2d", zmin=0.006, zmax=1)
    btag.plot_1d_hist(h_eff[flav], f"b-tag efficiency for {flav} jets", f"../../data/btagEff/plots/btag_eff_{flav}_{args.year}_1d", ymin=0.006, ymax=6)
btag.plot_1d_all_flavors(h_eff, f"../../data/btagEff/plots/btag_eff_all_flavors_{args.year}_1d", ymin=0.006, ymax=2)
