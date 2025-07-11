import streamlit as st
import pandas as pd
import re
from io import StringIO
import unicodedata

st.set_page_config(page_title="Org Chart Editor", layout="centered")
st.title("Org Chart Editor with Live Preview")

st.markdown("""
Paste your CSV below. Format:
Name,Title,ReportsTo
Alice,CEO,
Bob,VP of Sales,Alice
Carol,VP of Operations,Alice
Dana,Regional Manager East,Bob


Then enter natural commands to modify the org chart, like:
- `Move Dana under Carol`
- `Add Frank as Marketing Director reporting to Bob`
- `Remove Ethan`

The Mermaid chart and CSV output will update below.
""")

# Initial state
if 'df' not in st.session_state:
    st.session_state.df = pd.DataFrame(columns=["Name", "Title", "ReportsTo"])

# Input CSV
raw_csv = st.text_area("Paste your CSV here:", height=200)
if st.button("Load Chart") and raw_csv:
    try:
        st.session_state.df = pd.read_csv(StringIO(raw_csv))
        st.success("Chart loaded successfully.")
    except Exception as e:
        st.error(f"Error loading CSV: {e}")

# Normalize function for safe comparison
def normalize_name(name):
    return unicodedata.normalize('NFKD', str(name)).encode('ascii', 'ignore').decode('ascii').strip().lower()

# Input commands
command = st.text_input("Type your command:")
if st.button("Apply Command") and command:
    df = st.session_state.df.copy()
    cmd = command.strip()

    # MOVE
    m = re.match(r"Move (.+) under (.+)", cmd, re.IGNORECASE)
    if m:
        name, new_manager = m.groups()
        df.loc[df["Name"].apply(normalize_name) == normalize_name(name), "ReportsTo"] = new_manager

    # ADD
    a = re.match(r"Add (.+) as (.+) reporting to (.+)", cmd, re.IGNORECASE)
    if a:
        name, title, manager = a.groups()
        new_row = {"Name": name.strip(), "Title": title.strip(), "ReportsTo": manager.strip()}
        df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)

    # REMOVE
    r = re.match(r"Remove (.+)", cmd, re.IGNORECASE)
    if r:
        name = r.group(1).strip()
        df = df[df["Name"].apply(normalize_name) != normalize_name(name)]

    st.session_state.df = df
    st.success("Command applied.")

# Safe node name generator
def safe_node_name(name):
    name = str(name).strip()
    name = unicodedata.normalize('NFKD', name).encode('ascii', 'ignore').decode('ascii')
    return re.sub(r'[^a-zA-Z0-9_]', '_', name.replace(" ", "_"))

# Build Mermaid syntax
def generate_mermaid(df):
    links = []
    labels = []
    for _, row in df.iterrows():
        node_id = safe_node_name(row["Name"])
        label = f"{row['Name']}<br>{row['Title']}"
        labels.append(f"    {node_id}[\"{label}\"]")
        if pd.notna(row["ReportsTo"]):
            from_node = safe_node_name(row["ReportsTo"])
            links.append(f"    {from_node} --> {node_id}")
    return "graph TD\n" + "\n".join(labels + links)

# Mermaid chart preview using code block
st.subheader("📊 Org Chart Preview (Mermaid Syntax)")
mermaid_code = generate_mermaid(st.session_state.df)
st.code(mermaid_code, language="markdown")

# Export CSV
st.subheader("📝 Updated CSV Output")
csv_out = st.session_state.df.to_csv(index=False)
st.code(csv_out, language="csv")
st.download_button("Download CSV", csv_out, file_name="updated_org_chart.csv", mime="text/csv")
