#!/usr/bin/env python3
"""Plot nominal and paired JES/JER MELA probability variations.

Only the best ZZ candidate is plotted.  Requiring all three values to be
strictly positive excludes both the current -1 not-applicable sentinel and
zero sentinels in productions made before that convention changed.
"""

import argparse
import html
import re
from pathlib import Path

import ROOT


DEFAULT_INPUTS = {
    "ggH125": "/afs/cern.ch/user/g/geliu/EOS/HZZ4l_Run3/Ntuples/PROD_samplesNano_test_MC_918beac8/AAAOK/ggH125/ZZ4lAnalysis.root",
    "VBFH125": "/afs/cern.ch/user/g/geliu/EOS/HZZ4l_Run3/Ntuples/PROD_samplesNano_test_MC_918beac8/AAAOK/VBFH125/ZZ4lAnalysis.root",
}


def safe_name(value):
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", value)


def discover(tree):
    names = {branch.GetName() for branch in tree.GetListOfBranches()}
    nominal = sorted(
        name for name in names
        if name.startswith("ZZCand_P_") and "JECNominal" in name
    )
    variations = sorted({
        name[4:-3] for name in names
        if name.startswith("Jet_") and name.endswith("_pt")
        and ("ScaleUp" in name or "ScaleDn" in name
             or "smearUp" in name or "smearDn" in name)
    })
    pairs = []
    for up in variations:
        if up.endswith("ScaleUp"):
            down = up[:-2] + "Dn"
            nuisance = up[:-8]
        elif up == "smearUp":
            down = "smearDn"
            nuisance = "smear"
        else:
            continue
        if down in variations:
            pairs.append((nuisance, up, down))
    return nominal, pairs, names


def shifted_name(nominal, variation):
    return nominal.replace("JECNominal", variation, 1)


def quantity_label(branch):
    return branch.removeprefix("ZZCand_P_").replace("_JECNominal", "")


def book_histograms(path, max_events):
    root_file = ROOT.TFile.Open(path)
    if not root_file or root_file.IsZombie():
        raise OSError(f"Cannot open {path}")
    tree = root_file.Get("Events")
    nominal_branches, pairs, names = discover(tree)
    root_file.Close()

    if len(nominal_branches) != 11 or len(pairs) != 12:
        raise RuntimeError(
            f"Unexpected schema in {path}: {len(nominal_branches)} nominal "
            f"jet probabilities and {len(pairs)} Up/Down pairs"
        )

    frame = ROOT.RDataFrame("Events", path)
    if max_events >= 0:
        frame = frame.Filter(f"rdfentry_ < {max_events}")
    booked = []
    actions = []
    counter = 0
    for nominal in nominal_branches:
        for nuisance, up_variation, down_variation in pairs:
            up = shifted_name(nominal, up_variation)
            down = shifted_name(nominal, down_variation)
            if up not in names or down not in names:
                raise RuntimeError(f"Missing {up} or {down}")
            token = f"p{counter}"
            counter += 1
            valid = (
                f"bestCandIdx>=0 && bestCandIdx<{nominal}.size() && "
                f"bestCandIdx<{up}.size() && bestCandIdx<{down}.size() && "
                f"{nominal}[bestCandIdx]>0.f && {up}[bestCandIdx]>0.f && "
                f"{down}[bestCandIdx]>0.f"
            )
            node = (
                frame.Filter(valid)
                .Define(f"{token}_nom", f"log10(double({nominal}[bestCandIdx]))")
                .Define(f"{token}_up", f"log10(double({up}[bestCandIdx]))")
                .Define(f"{token}_down", f"log10(double({down}[bestCandIdx]))")
            )
            model = ("", "", 140, -30.0, 5.0)
            h_nom = node.Histo1D(model, f"{token}_nom")
            h_up = node.Histo1D(model, f"{token}_up")
            h_down = node.Histo1D(model, f"{token}_down")
            count = node.Count()
            actions.extend((h_nom, h_up, h_down, count))
            booked.append((nominal, nuisance, h_nom, h_up, h_down, count))
    return booked, actions


def normalize(hist):
    clone = hist.Clone(hist.GetName() + "_normalized")
    clone.SetDirectory(0)
    integral = clone.Integral(0, clone.GetNbinsX() + 1)
    if integral:
        clone.Scale(1.0 / integral)
    return clone


def render(sample, booked, output):
    output.mkdir(parents=True, exist_ok=True)
    entries = []
    for nominal, nuisance, h_nom_result, h_up_result, h_down_result, count_result in booked:
        h_nom = normalize(h_nom_result.GetValue())
        h_up = normalize(h_up_result.GetValue())
        h_down = normalize(h_down_result.GetValue())
        valid_count = int(count_result.GetValue())

        quantity = quantity_label(nominal)
        filename = f"{safe_name(quantity)}__{safe_name(nuisance)}.png"
        canvas = ROOT.TCanvas("canvas", "canvas", 850, 800)
        upper = ROOT.TPad("upper", "upper", 0.0, 0.29, 1.0, 1.0)
        lower = ROOT.TPad("lower", "lower", 0.0, 0.0, 1.0, 0.29)
        upper.SetBottomMargin(0.02)
        upper.SetLeftMargin(0.13)
        upper.SetRightMargin(0.04)
        upper.SetLogy()
        lower.SetTopMargin(0.03)
        lower.SetBottomMargin(0.34)
        lower.SetLeftMargin(0.13)
        lower.SetRightMargin(0.04)
        lower.SetGridy()
        upper.Draw()
        lower.Draw()

        upper.cd()
        for hist, color in ((h_nom, ROOT.kBlack), (h_up, ROOT.kRed + 1),
                            (h_down, ROOT.kBlue + 1)):
            hist.SetLineColor(color)
            hist.SetLineWidth(2)
        maximum = max(h_nom.GetMaximum(), h_up.GetMaximum(), h_down.GetMaximum())
        positive_bins = [
            hist.GetBinContent(i)
            for hist in (h_nom, h_up, h_down)
            for i in range(1, hist.GetNbinsX() + 1)
            if hist.GetBinContent(i) > 0
        ]
        minimum = min(positive_bins) if positive_bins else 1e-7
        h_nom.SetMinimum(max(minimum * 0.45, 1e-8))
        h_nom.SetMaximum(maximum * 8.0 if maximum else 1.0)
        h_nom.GetYaxis().SetTitle("Fraction of valid events / bin")
        h_nom.GetYaxis().SetTitleOffset(1.55)
        h_nom.GetXaxis().SetLabelSize(0)
        h_nom.SetTitle(f"{sample}: {quantity};log_{{10}}(P);Fraction")
        h_nom.Draw("HIST")
        h_up.Draw("HIST SAME")
        h_down.Draw("HIST SAME")
        legend = ROOT.TLegend(0.61, 0.72, 0.94, 0.89)
        legend.SetBorderSize(0)
        legend.SetFillStyle(0)
        legend.AddEntry(h_nom, "Nominal", "l")
        legend.AddEntry(h_up, f"{nuisance} Up", "l")
        legend.AddEntry(h_down, f"{nuisance} Down", "l")
        legend.Draw()
        label = ROOT.TLatex()
        label.SetNDC()
        label.SetTextSize(0.032)
        label.DrawLatex(0.14, 0.92, f"Valid best-candidate events: {valid_count}")

        lower.cd()
        ratio_up = h_up.Clone("ratio_up")
        ratio_down = h_down.Clone("ratio_down")
        ratio_up.Divide(h_nom)
        ratio_down.Divide(h_nom)
        ratio_up.SetMinimum(0.5)
        ratio_up.SetMaximum(1.5)
        ratio_up.SetTitle("")
        ratio_up.GetYaxis().SetTitle("Var/Nom")
        ratio_up.GetYaxis().SetNdivisions(505)
        ratio_up.GetYaxis().SetTitleSize(0.10)
        ratio_up.GetYaxis().SetTitleOffset(0.55)
        ratio_up.GetYaxis().SetLabelSize(0.08)
        ratio_up.GetXaxis().SetTitle("log_{10}(MELA probability)")
        ratio_up.GetXaxis().SetTitleSize(0.12)
        ratio_up.GetXaxis().SetTitleOffset(1.05)
        ratio_up.GetXaxis().SetLabelSize(0.09)
        ratio_up.Draw("HIST")
        ratio_down.Draw("HIST SAME")
        canvas.SaveAs(str(output / filename))
        entries.append((filename, quantity, nuisance, valid_count))
        canvas.Close()

    with (output / "index.html").open("w", encoding="utf-8") as handle:
        handle.write(f"<html><body><h1>{html.escape(sample)} jet-varied MELA</h1>\n")
        handle.write("<p>Best candidate only; nominal, Up, and Down all &gt; 0.</p>\n")
        for filename, quantity, nuisance, count in entries:
            handle.write(
                f"<h3>{html.escape(quantity)} — {html.escape(nuisance)} "
                f"({count} events)</h3><img src='{html.escape(filename)}' width='700'>\n"
            )
        handle.write("</body></html>\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--threads", type=int, default=4)
    parser.add_argument("--max-events", type=int, default=-1)
    parser.add_argument("--ggH125", default=DEFAULT_INPUTS["ggH125"])
    parser.add_argument("--VBFH125", default=DEFAULT_INPUTS["VBFH125"])
    args = parser.parse_args()

    ROOT.gROOT.SetBatch(True)
    ROOT.gStyle.SetOptStat(0)
    if args.threads > 1:
        ROOT.EnableImplicitMT(args.threads)
    for sample, path in (("ggH125", args.ggH125), ("VBFH125", args.VBFH125)):
        print(f"[plotJetVariedMELA] Booking {sample}: {path}", flush=True)
        booked, actions = book_histograms(path, args.max_events)
        print(f"[plotJetVariedMELA] Running {len(actions)} actions", flush=True)
        ROOT.RDF.RunGraphs(actions)
        print(f"[plotJetVariedMELA] Rendering {len(booked)} plots", flush=True)
        render(sample, booked, args.output / sample)
    print(f"[plotJetVariedMELA] Output: {args.output.resolve()}")


if __name__ == "__main__":
    main()
