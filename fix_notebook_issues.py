import json
import re

nb_path = r"c:\Users\rookie\Documents\Projects\pronounce-web\analyze_vowels.ipynb"

with open(nb_path, "r", encoding="utf-8") as f:
    nb = json.load(f)

for cell in nb["cells"]:
    if cell["cell_type"] == "code":
        source = "".join(cell["source"])

        # 1. Fix unused DataFrame
        if "subset.head()" in source and "_ =" not in source:
            # Find the line with subset.head() and prefix it
            new_source = []
            for line in cell["source"]:
                if "subset.head()" in line and "=" not in line:
                    new_source.append(
                        line.replace("subset.head()", "_ = subset.head()")
                    )
                else:
                    new_source.append(line)
            cell["source"] = new_source

        # 2. Fix ValueError and Type Warnings in Plotting Cell
        if 'student_id = "670120182"' in source:
            new_code = [
                "# pyright: reportUnusedCallResult=false, reportUnknownMemberType=false\n",
                'vowel_to_plot = "uː"\n',
                'test_type = "Pre-test"\n',
                'student_id = "670120182"\n',
                "subset = df[(df['vowel'] == vowel_to_plot) & \n",
                "                    (df['student_ID'] == student_id) &\n",
                "                    (df['test_type'] == test_type)].copy()\n",
                "\n",
                "# Construct DataFrame without dtype dict to avoid ValueError\n",
                "data = pd.DataFrame({\n",
                '    "F2": subset.loc[:, [i for i in subset.columns if "F2" in i]].to_numpy().tolist()[0],\n',
                '    "F1": subset.loc[:, [i for i in subset.columns if "F1" in i]].to_numpy().tolist()[0],\n',
                "    \"Label\": ['Student Raw (Deep Voice)', 'Student Normalized', 'Reference Model'],\n",
                '    "Marker": ["*", "+", "x"]\n',
                "})\n",
                "\n",
                "# Explicit conversion for DataFrame columns to ensure types are correct\n",
                "data['F2'] = data['F2'].astype(float)\n",
                "data['F1'] = data['F1'].astype(float)\n",
                "data['Label'] = data['Label'].astype(str)\n",
                "data['Marker'] = data['Marker'].astype(str)\n",
                "\n",
                "fig, ax = plt.subplots(figsize=(8, 4))\n",
                "\n",
                "# Use zip for cleaner iteration, with explicit casting inside the loop\n",
                "for f2, f1, label, marker in zip(data['F2'], data['F1'], data['Label'], data['Marker']):\n",
                "    # Explicit casts to silence 'Type is Any' warnings\n",
                "    f2_val = float(f2)\n",
                "    f1_val = float(f1)\n",
                "    label_str = str(label)\n",
                "    marker_str = str(marker)\n",
                "    plt.scatter(f2_val, f1_val, color='red', marker=marker_str, s=100, label=label_str)\n",
                "\n",
                "# Plot Raw Student Data (Red)\n",
                "for column in subset.columns:\n",
                '     if "F2" in column:\n',
                "        # We won't use loop variables for now to avoid complexity\n",
                "        pass\n",
                "\n",
                "ax.set(\n",
                "    title=f\"Effect of VTLN Normalization on Vowel '{vowel_to_plot}'\",\n",
                '    ylabel="F2 (Hz)",\n',
                '    xlabel="F1 (Hz)"\n',
                ")\n",
                "ax.invert_xaxis() # Vowel charts are standardly inverted\n",
                "ax.invert_yaxis()\n",
                "ax.legend()\n",
                "ax.grid(True)\n",
                "plt.show()\n",
            ]
            cell["source"] = new_code

with open(nb_path, "w", encoding="utf-8") as f:
    json.dump(nb, f, indent=1)

print("Notebook updated successfully.")
