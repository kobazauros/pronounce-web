import shutil
from operator import index
import pathlib
import pandas as pd
import re
import shutil

# Step 1: Efficient Data Loading
# We build a list of dictionaries first, then create the DataFrame once.
# This prevents the expensive operation of resizing the DataFrame for every row.
data = []
root_dir = pathlib.Path(__file__).parent.parent.resolve()
# audio_dir = root_dir / "samples"
# INPUT: Archived raw samples
audio_dir = root_dir / "archive" / "raw_forvo_samples" / "samples"

# OUTPUT: New dataset location
audio_dir_new = root_dir / "dataset" / "forvo"

# Iterate using pathlib which is more robust and cleaner
for word_dir in audio_dir.iterdir():
    if not word_dir.is_dir():
        continue

    for audio_file in word_dir.iterdir():
        if audio_file.suffix != ".mp3":
            continue

        # Extract metadata using regex
        # Format: {nickname}_{gender}_{country}.mp3
        match = re.search(r"(.+)_(male|female)_(.+)", audio_file.stem)
        if match:
            data.append(
                {
                    "nickname": match.group(1),
                    "sex": match.group(2),
                    "country": match.group(3),
                    "word": word_dir.name,
                    "path": str(audio_file),
                }
            )

# Create DataFrame in one go
df = pd.DataFrame(data)
# Step 2: Vectorized Matrix Construction
# Instead of iterating through every user and every word to build a row manually,
# we use pandas' built-in `crosstab` function which computes this matrix in vectorized C code.
# This transforms the long-form data (one row per file) into wide-form (one row per user).

# Create a presence matrix: Rows=Users, Cols=Words.
# values=1 if present, 0 if absent.
df_words = pd.crosstab(df["nickname"], df["word"]).astype(bool)

# Reset index to make 'nickname' a column again, matching the original 'user' column
df_words = df_words.reset_index().rename(columns={"nickname": "user"})

# Ensure columns are sorted to match original output (optional but good for consistency)
# 'user' first, then words sorted alphabetically
cols = ["user"] + sorted([c for c in df_words.columns if c != "user"])
df_words = df_words[cols]

# Step 3: Efficient Filtering (Heuristic Sorting)
# The greedy filtering algorithm is sensitive to row order.
# By processing "rich" users (those with many words) first, we can likely satisfy
# the requirements with fewer total users, resulting in a cleaner dataset.

# Calculate "richness" (number of words per user)
# Note: slicing [1:] excludes the 'user' column
df_words["word_count"] = df_words.iloc[:, 1:].sum(axis=1)

# Sort by richness descending
df_words = df_words.sort_values(by=["word_count"], ascending=False)  # type: ignore
df_words = df_words.drop("word_count", axis=1)  # Clean up helper col

# Initialize counters for each word column
word_cols = [c for c in df_words.columns if c != "user"]
counts = {col: 0 for col in word_cols}
keep_indices = []

# Iterate row-by-row
for index, row in df_words.iterrows():
    keep_this_row = False

    for col in word_cols:
        # Check if user has this word AND we haven't reached the target of 3 yet
        # Since df_words is bool type, row[col] is a boolean.
        if row[col] and counts[col] < 3:  # type: ignore
            counts[col] += 1
            keep_this_row = True

    if keep_this_row:
        keep_indices.append(index)

# 3. Prune the dataframe
df_pruned = df_words.loc[keep_indices]

print(df_pruned.shape)

true_counts = df_pruned.drop("user", axis=1).sum()

print(true_counts.sum())

df_path_pruned = df[df["nickname"].isin(df_pruned["user"])]

print(df_path_pruned.shape)

# audio_dir_new defined above
# audio_dir_new = root_dir / "samples_new"
for word_dir in audio_dir.iterdir():
    new_dir = audio_dir_new / word_dir.name
    new_dir.mkdir(exist_ok=True)
for index, row in df_path_pruned.iterrows():
    shutil.copy(
        str(row["path"]),
        str(audio_dir_new / row["word"] / str(row["nickname"]))
        + "_"
        + str(row["sex"])
        + "_"
        + str(row["country"])
        + ".mp3",
    )
