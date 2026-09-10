from datetime import datetime
import os
import time
import requests
from PIL import Image
import streamlit as st

# Configure page
st.set_page_config(
    page_title="Zack Image Generator", page_icon="🎨", layout="centered"
)

# Constants
MAX_DAILY_IMAGES = 100
DATE_FILE = "last_date.txt"
COUNT_FILE = "image_count.txt"


def get_daily_count():
  today = datetime.now().strftime("%Y-%m-%d")

  # Check stored date
  stored_date = ""
  if os.path.exists(DATE_FILE):
    with open(DATE_FILE, "r") as f:
      stored_date = f.read().strip()

  # Reset if new day
  if stored_date != today:
    with open(DATE_FILE, "w") as f:
      f.write(today)
    with open(COUNT_FILE, "w") as f:
      f.write("0")
    return 0

  # Read current count
  if os.path.exists(COUNT_FILE):
    with open(COUNT_FILE, "r") as f:
      try:
        return int(f.read().strip())
      except ValueError:
        return 0
  return 0


def increment_count():
  current = get_daily_count()
  with open(COUNT_FILE, "w") as f:
    f.write(str(current + 1))


# UI Layout
st.title("Zack AI Image Generator")
st.markdown("Generate consistent images of **Zack** with custom backgrounds.")

# Sidebar for API token and stats
st.sidebar.header("Configuration")
api_token = st.sidebar.text_input("Replicate API Token", type="password")

daily_used = get_daily_count()
st.sidebar.metric(
    label="Images Left Today", value=max(0, MAX_DAILY_IMAGES - daily_used)
)

# Main inputs
prompt_core = st.text_input(
    "What is Zack doing?",
    placeholder="e.g., Zack drinking coffee in a cyberpunk cafe",
)
consistency_tag = st.text_input(
    "Character/Background Consistency Anchor",
    value="A 25-year-old man named Zack with short brown hair, wearing a blue jacket,",
    help=(
        "Keep this exact phrase in all generations to maintain character"
        " consistency."
    ),
)
background_tag = st.text_input(
    "Background Setting", value="detailed cinematic lighting, 8k resolution"
)

if st.button("Generate Image"):
  if not api_token:
    st.error("Please enter your Replicate API Token in the sidebar.")
  elif daily_used >= MAX_DAILY_IMAGES:
    st.error("Daily limit of 100 images reached! Try again tomorrow.")
  elif not prompt_core:
    st.warning("Please describe what Zack is doing.")
  else:
    full_prompt = f"{consistency_tag} {prompt_core}, {background_tag}"

    with st.spinner("Generating Zack's image..."):
      headers = {
          "Authorization": f"Bearer {api_token}",
          "Content-Type": "application/json",
      }
      # Using Stable Diffusion XL on Replicate
      data = {
          "version": (
              "39ed52f2a78e934b3ba6e2a89f5b1c712de7dfea535525255b1aa35c5565e08b"
          ),
          "input": {"prompt": full_prompt},
      }

      response = requests.post(
          "https://replicate.com",
          headers=headers,
          json=data,
      )

      if response.status_code != 201:
        st.error(f"Error starting generation: {response.text}")
      else:
        prediction = response.json()
        get_url = prediction["urls"]["get"]

        # Poll for completion
        image_url = None
        for _ in range(30):
          time.sleep(2)
          poll_res = requests.get(get_url, headers=headers).json()
          if poll_res.get("status") == "succeeded":
            image_url = poll_res["output"][0]
            break
          elif poll_res.get("status") == "failed":
            st.error("Generation failed.")
            break

        if image_url:
          increment_count()
          st.success("Image generated successfully!")
          st.image(image_url, caption=full_prompt)

