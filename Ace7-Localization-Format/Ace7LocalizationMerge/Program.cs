using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using Ace7Ed;
using Ace7LocalizationFormat.Formats;

namespace Ace7LocalizationMerge;

internal static class Program
{
    private const int ExpectedDatCount = 13;

    public static int Main(string[] args)
    {
        if (args.Length != 3)
        {
            Console.Error.WriteLine("Usage: Ace7LocalizationMerge <merge|replace> <sourceFolder> <targetFolder>");
            return 1;
        }

        string mode = args[0].Trim().ToLowerInvariant();
        string sourceFolder = args[1].Trim();
        string targetFolder = args[2].Trim();

        if (mode != "merge" && mode != "replace")
        {
            Console.Error.WriteLine("Mode must be 'merge' or 'replace'.");
            return 1;
        }

        if (!Directory.Exists(sourceFolder))
        {
            Console.Error.WriteLine($"Source folder not found: {sourceFolder}");
            return 1;
        }

        if (!Directory.Exists(targetFolder))
        {
            Console.Error.WriteLine($"Target folder not found: {targetFolder}");
            return 1;
        }

        try
        {
            (CMN sourceCmn, List<DAT> sourceDats) = LoadLocalization(sourceFolder);
            (CMN targetCmn, List<DAT> targetDats) = LoadLocalization(targetFolder);

            if (mode == "merge")
            {
                MergeLocalization(sourceCmn, sourceDats, targetCmn, targetDats);
            }
            else
            {
                ReplaceLocalization(sourceCmn, sourceDats, targetCmn, targetDats);
            }

            EnsureTargetDatsPadded(targetCmn, targetDats);
            SaveLocalization(targetFolder, targetCmn, targetDats);

            Console.WriteLine("[Localization] Done.");
            return 0;
        }
        catch (Exception ex)
        {
            Console.Error.WriteLine($"[Localization] Error: {ex.Message}");
            return 1;
        }
    }

    private static (CMN cmn, List<DAT> dats) LoadLocalization(string folder)
    {
        string cmnPath = Path.Combine(folder, "Cmn.dat");
        if (!File.Exists(cmnPath))
            throw new FileNotFoundException($"Cmn.dat not found in {folder}");

        var cmn = new CMN(cmnPath);
        var dats = new List<DAT>();

        foreach (char letter in AceLocalizationConstants.DatLetters.Keys.OrderBy(c => c))
        {
            string datPath = Path.Combine(folder, $"{letter}.dat");
            if (!File.Exists(datPath))
                throw new FileNotFoundException($"{letter}.dat not found in {folder}");
            dats.Add(new DAT(datPath, letter));
        }

        if (dats.Count != ExpectedDatCount)
            throw new InvalidOperationException($"Expected {ExpectedDatCount} DAT files, found {dats.Count}");

        return (cmn, dats);
    }

    private static void SaveLocalization(string folder, CMN cmn, List<DAT> dats)
    {
        string cmnPath = Path.Combine(folder, "Cmn.dat");
        string cmnBakPath = cmnPath + ".bak";
        if (File.Exists(cmnPath) && !File.Exists(cmnBakPath))
        {
            File.Copy(cmnPath, cmnBakPath);
            Console.WriteLine($"[Localization] Backup created: {cmnBakPath}");
        }
        cmn.Write(cmnPath);

        foreach (var dat in dats)
        {
            string datPath = Path.Combine(folder, $"{dat.Letter}.dat");
            string datBakPath = datPath + ".bak";
            if (File.Exists(datPath) && !File.Exists(datBakPath))
            {
                File.Copy(datPath, datBakPath);
                Console.WriteLine($"[Localization] Backup created: {datBakPath}");
            }
            dat.Write(datPath, dat.Letter);
        }
    }

    /// <summary>
    /// Pad target DATs so each has at least (MaxStringNumber + 1) strings.
    /// </summary>
    private static void EnsureTargetDatsPadded(CMN targetCmn, List<DAT> targetDats)
    {
        int required = targetCmn.MaxStringNumber + 1;
        foreach (var dat in targetDats)
        {
            while (dat.Strings.Count < required)
                dat.Strings.Add("\0");
        }
    }

    /// <summary>
    /// Collect all CMN nodes that have a string (StringNumber >= 0).
    /// </summary>
    private static IEnumerable<CMN.CmnString> EnumerateStringNodes(CMN.CmnString parent)
    {
        foreach (var child in parent.Childrens)
        {
            if (child.StringNumber >= 0)
                yield return child;
            foreach (var desc in EnumerateStringNodes(child))
                yield return desc;
        }
    }

    /// <summary>
    /// Merge: add all source variables/strings into target (like Import Localization).
    /// </summary>
    private static void MergeLocalization(CMN sourceCmn, List<DAT> sourceDats, CMN targetCmn, List<DAT> targetDats)
    {
        var nodesToVisit = new List<CMN.CmnString> { sourceCmn.Root };
        int index = 0;

        while (index < nodesToVisit.Count)
        {
            CMN.CmnString cmnString = nodesToVisit[index];
            foreach (var child in cmnString.Childrens)
            {
                bool added = targetCmn.AddVariable(child.FullName, targetCmn.Root, out int variableStringNumber, child.StringNumber == -1);

                if (child.StringNumber != -1)
                {
                    for (int i = 0; i < sourceDats.Count && i < targetDats.Count; i++)
                    {
                        string sourceStr = child.StringNumber < sourceDats[i].Strings.Count
                            ? sourceDats[i].Strings[child.StringNumber]
                            : "\0";
                        if (added)
                            targetDats[i].Strings.Add(sourceStr);
                        else
                            targetDats[i].Strings[variableStringNumber] = sourceStr;
                    }
                }
                nodesToVisit.Add(child);
            }
            index++;
        }
    }

    /// <summary>
    /// Replace: add new variables; for existing ones, overwrite only if target is empty and source has text;
    /// otherwise if both have different text, log for manual edit.
    /// </summary>
    private static void ReplaceLocalization(CMN sourceCmn, List<DAT> sourceDats, CMN targetCmn, List<DAT> targetDats)
    {
        foreach (var sourceNode in EnumerateStringNodes(sourceCmn.Root))
        {
            string fullName = sourceNode.FullName;
            bool existsInTarget = !targetCmn.CheckVariableExist(fullName);

            if (!existsInTarget)
            {
                // New variable: add to target and copy strings
                bool added = targetCmn.AddVariable(fullName, targetCmn.Root, out int variableStringNumber, sourceNode.StringNumber == -1);
                if (sourceNode.StringNumber != -1)
                {
                    for (int i = 0; i < sourceDats.Count && i < targetDats.Count; i++)
                    {
                        string sourceStr = sourceNode.StringNumber < sourceDats[i].Strings.Count
                            ? sourceDats[i].Strings[sourceNode.StringNumber]
                            : "\0";
                        if (added)
                            targetDats[i].Strings.Add(sourceStr);
                        else
                            targetDats[i].Strings[variableStringNumber] = sourceStr;
                    }
                }
                continue;
            }

            // Existing variable: overwrite only when target empty and source has text; else log conflicts
            int targetStrNum = targetCmn.GetVariableStringNumber(fullName);
            if (targetStrNum < 0)
                continue;

            for (int i = 0; i < sourceDats.Count && i < targetDats.Count; i++)
            {
                if (targetStrNum >= targetDats[i].Strings.Count)
                    continue;

                string targetStr = targetDats[i].Strings[targetStrNum];
                string sourceStr = sourceNode.StringNumber < sourceDats[i].Strings.Count
                    ? sourceDats[i].Strings[sourceNode.StringNumber]
                    : "";

                bool targetEmpty = string.IsNullOrEmpty(targetStr?.Trim());
                bool sourceHasText = !string.IsNullOrEmpty(sourceStr?.Trim());

                if (targetEmpty && sourceHasText)
                {
                    targetDats[i].Strings[targetStrNum] = sourceStr ?? "";
                }
                else if (!targetEmpty && sourceHasText && targetStr != sourceStr)
                {
                    string langName = targetDats[i].Language ?? $"{targetDats[i].Letter}";
                    Console.WriteLine($"[Localization] Variable: {fullName} | Language: {langName} ({targetDats[i].Letter}) - requires manual edit");
                }
            }
        }
    }
}
