#!/usr/bin/env python3
"""Plot event-by-event varied/nominal MELA probability ratios."""

import argparse
import html
from pathlib import Path

import ROOT

from plotJetVariedMELA import (
    DEFAULT_INPUTS,
    discover,
    quantity_label,
    safe_name,
    shifted_name,
)


def book_ratios(path, max_events):
    root_file = ROOT.TFile.Open(path)
    if not root_file or root_file.IsZombie():
        raise OSError(f"Cannot open {path}")
    tree = root_file.Get("Events")
    nominal_branches, pairs, names = discover(tree)
    root_file.Close()
    if len(nominal_branches) != 11 or len(pairs) != 12:
        raise RuntimeError(
            f"Unexpected schema: {len(nominal_branches)} probabilities, "
            f"{len(pairs)} Up/Down pairs"
        )

    frame = ROOT.RDataFrame("Events", path)
    if max_events >= 0:
        frame = frame.Filter(f"rdfentry_ < {max_events}")
    booked, actions = [], []
    counter = 0
    for nominal in nominal_branches:
        for nuisance, up_variation, down_variation in pairs:
            up = shifted_name(nominal, up_variation)
            down = shifted_name(nominal, down_variation)
            if up not in names or down not in names:
                raise RuntimeError(f"Missing {up} or {down}")
            token = f"ratio{counter}"
            counter += 1
            valid = (
                f"bestCandIdx>=0 && bestCandIdx<{nominal}.size() && "
                f"bestCandIdx<{up}.size() && bestCandIdx<{down}.size() && "
                f"{nominal}[bestCandIdx]>0.f && {up}[bestCandIdx]>0.f && "
                f"{down}[bestCandIdx]>0.f"
            )
            node = (
                frame.Filter(valid)
                .Define(
                    f"{token}_up",
                    f"double({up}[bestCandIdx])/{nominal}[bestCandIdx]",
                )
                .Define(
                    f"{token}_down",
                    f"double({down}[bestCandIdx])/{nominal}[bestCandIdx]",
                )
            )
            model = ("", "", 150, 0.0, 3.0)
            h_up = node.Histo1D(model, f"{token}_up")
            h_down = node.Histo1D(model, f"{token}_down")
            count = node.Count()
            actions.extend((h_up, h_down, count))
            booked.append((nominal, nuisance, h_up, h_down, count))
    return booked, actions


def normalized(result, suffix):
    hist = result.GetValue().Clone(result.GetValue().GetName() + suffix)
    hist.SetDirectory(0)
    integral = hist.Integral(0, hist.GetNbinsX() + 1)
    if integral:
        hist.Scale(1.0 / integral)
    return hist


def render(sample, booked, output):
    output.mkdir(parents=True, exist_ok=True)
    entries = []
    for nominal, nuisance, up_result, down_result, count_result in booked:
        up = normalized(up_result, "_up_normalized")
        down = normalized(down_result, "_down_normalized")
        valid_count = int(count_result.GetValue())
        quantity = quantity_label(nominal)
        filename = f"{safe_name(quantity)}__{safe_name(nuisance)}__ratio.png"

        canvas = ROOT.TCanvas("ratio_canvas", "ratio_canvas", 850, 700)
        canvas.SetLeftMargin(0.13)
        canvas.SetRightMargin(0.04)
        canvas.SetBottomMargin(0.13)
        canvas.SetLogy()
        up.SetLineColor(ROOT.kRed + 1)
        down.SetLineColor(ROOT.kBlue + 1)
        up.SetLineWidth(2)
        down.SetLineWidth(2)
        maximum = max(up.GetMaximum(), down.GetMaximum())
        positive = [
            hist.GetBinContent(index)
            for hist in (up, down)
            for index in range(1, hist.GetNbinsX() + 1)
            if hist.GetBinContent(index) > 0
        ]
        minimum = min(positive) if positive else 1e-7
        up.SetMinimum(max(minimum * 0.45, 1e-8))
        up.SetMaximum(maximum * 8.0 if maximum else 1.0)
        up.SetTitle(
            f"{sample}: {quantity};"
            "P_{variation}/P_{nominal};Fraction of valid events / bin"
        )
        up.GetYaxis().SetTitleOffset(1.55)
        up.Draw("HIST")
        down.Draw("HIST SAME")

        unity_line = ROOT.TLine(1.0, up.GetMinimum(), 1.0, up.GetMaximum())
        unity_line.SetLineStyle(2)
        unity_line.SetLineColor(ROOT.kGray + 2)
        unity_line.Draw()
        legend = ROOT.TLegend(0.60, 0.73, 0.94, 0.88)
        legend.SetBorderSize(0)
        legend.SetFillStyle(0)
        legend.AddEntry(up, f"{nuisance} Up / nominal", "l")
        legend.AddEntry(down, f"{nuisance} Down / nominal", "l")
        legend.Draw()
        label = ROOT.TLatex()
        label.SetNDC()
        label.SetTextSize(0.032)
        label.DrawLatex(0.14, 0.84, f"Valid best-candidate events: {valid_count}")
        label.DrawLatex(0.14, 0.795, "Dashed line: ratio = 1")
        up_overflow = 100.0 * up.GetBinContent(up.GetNbinsX() + 1)
        down_overflow = 100.0 * down.GetBinContent(down.GetNbinsX() + 1)
        label.DrawLatex(
            0.14, 0.75,
            f"Ratio > 3: Up {up_overflow:.3g}%, Down {down_overflow:.3g}%",
        )
        canvas.SaveAs(str(output / filename))
        canvas.Close()
        entries.append((filename, quantity, nuisance, valid_count))

    with (output / "index.html").open("w", encoding="utf-8") as handle:
        handle.write(f"<html><body><h1>{html.escape(sample)} MELA ratios</h1>\n")
        handle.write(
            "<p>Best candidate only; nominal, Up, and Down all &gt; 0. "
            "The linear x axis is Pvariation/Pnominal; the dashed line is 1. "
            "Each plot reports the overflow above 3.</p>\n"
        )
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
        print(f"[plotJetVariedMELARatios] Booking {sample}", flush=True)
        booked, actions = book_ratios(path, args.max_events)
        ROOT.RDF.RunGraphs(actions)
        print(f"[plotJetVariedMELARatios] Rendering {len(booked)} plots", flush=True)
        render(sample, booked, args.output / sample)
    print(f"[plotJetVariedMELARatios] Output: {args.output.resolve()}")


if __name__ == "__main__":
    main()
