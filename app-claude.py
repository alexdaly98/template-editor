import streamlit as st
import requests
from writerai import Writer
from io import BytesIO
from PIL import Image
import os

st.set_page_config(page_title="AI Template Editor", layout="wide")

st.title("🎨 AI-Powered Template Editor")

# Get API keys from environment variables
writer_api_key = os.getenv('WRITER_API_KEY')
photoroom_api_key = os.getenv('PHOTOROOM_API_KEY')

# Sidebar for configuration
with st.sidebar:
    st.header("⚙️ Configuration")
    template_id = st.text_input("Template ID", value="a8eed145-f813-4d60-b227-8015dac1889b")

# Main content
st.header("📝 Step 1: Generate Header & CTA Variants")

brief = st.text_area(
    "Marketing Brief",
    value="Christmas campaign for Pelican (Cases, Flashlights, Coolers, Travel Gear) \nHeader should be 4 words max and ALL CAPS\nCTA invites users to browse the website",
    help="Describe the marketing campaign - we'll generate header and CTA button text pairs. Include any specific instructions for header or CTA"
)

# Fixed layer IDs and descriptions
layer_id_1 = "header"
layer_id_2 = "cta"
layer_1_description = "Header"
layer_2_description = "CTA"

if st.button("🚀 Generate 10 Header & CTA Variants", type="primary", use_container_width=True):
    if not writer_api_key:
        st.error("❌ Writer API key not found in environment variables")
    else:
        with st.spinner("Generating variant couples..."):
            try:
                # Initialize Writer client
                client = Writer(api_key=writer_api_key)
                
                # Generate variant couples
                completion = client.completions.create(
                    model="palmyra-x-003-instruct",
                    prompt=f"""Generate 10 different marketing variant couples for {brief}.
                    
For each couple, provide:
- A catchy header/headline
- A compelling CTA (call-to-action) button text

Format each couple exactly like this:
1. Header: [header text]
   CTA: [CTA button text]

Make them punchy and effective for marketing. Generate all 10 couples numbered 1-10.""",
                    max_tokens=1000
                )
                
                # Parse variant couples
                text = completion.choices[0].text
                lines = [line.strip() for line in text.split('\n') if line.strip()]
                
                # Extract couples
                couples = []
                current_couple = {}
                
                for line in lines:
                    if 'Header:' in line or 'header:' in line.lower():
                        text = line.split(':', 1)[-1].strip()
                        current_couple['layer1'] = text
                    elif 'CTA:' in line or 'cta:' in line.lower():
                        text = line.split(':', 1)[-1].strip()
                        current_couple['layer2'] = text
                        if 'layer1' in current_couple:
                            couples.append(current_couple.copy())
                            current_couple = {}
                
                # Ensure we have exactly 10 couples
                couples = couples[:10]
                
                if len(couples) < 10:
                    st.warning(f"⚠️ Only generated {len(couples)} couples. You may want to try again.")
                
                # Store in session state
                st.session_state['couples'] = couples
                st.session_state['selected_couples'] = []
                
                st.success(f"✅ Generated {len(couples)} variant couples!")
                
            except Exception as e:
                st.error(f"❌ Error generating variants: {str(e)}")

# Display variant couples if they exist
if 'couples' in st.session_state and st.session_state['couples']:
    st.divider()
    st.header("✅ Step 2: Select Header & CTA Variants")
    
    # Create checkboxes for each couple
    selected_indices = []
    
    for idx, couple in enumerate(st.session_state['couples']):
        with st.container():
            col1, col2 = st.columns([1, 20])
            
            with col1:
                selected = st.checkbox("", key=f"couple_{idx}", label_visibility="collapsed")
                if selected:
                    selected_indices.append(idx)
            
            with col2:
                st.markdown(f"""
                **Variant {idx + 1}:**
                - **Header:** {couple.get('layer1', 'N/A')}
                - **CTA:** {couple.get('layer2', 'N/A')}
                """)
        
        if idx < len(st.session_state['couples']) - 1:
            st.divider()
    
    st.session_state['selected_couples'] = selected_indices
    
    # Generate images button
    st.divider()
    if st.button("🖼️ Generate Images for Selected Variants", type="primary", use_container_width=True):
        if not photoroom_api_key:
            st.error("❌ PhotoRoom API key not found in environment variables")
        elif not template_id:
            st.error("❌ Please enter Template ID in the sidebar")
        elif len(selected_indices) == 0:
            st.warning("⚠️ Please select at least one header & CTA variant")
        else:
            st.header("🎨 Generated Images")
            
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            generated_images = []
            
            for i, idx in enumerate(selected_indices):
                couple = st.session_state['couples'][idx]
                layer1_text = couple.get('layer1', '')
                layer2_text = couple.get('layer2', '')
                
                status_text.text(f"Generating image {i+1}/{len(selected_indices)}...")
                
                try:
                    # Prepare form data with both layers
                    form_data = {
                        "templateId": (None, template_id),
                        f"layers.{layer_id_1}.text.content": (None, layer1_text),
                        f"layers.{layer_id_2}.text.content": (None, layer2_text)
                    }
                    
                    # Make API request
                    response = requests.post(
                        "https://image-api.photoroom.com/v2/edit",
                        headers={"x-api-key": photoroom_api_key},
                        files=form_data
                    )
                    
                    if response.status_code == 200:
                        # Convert to PIL Image
                        img = Image.open(BytesIO(response.content))
                        generated_images.append({
                            'layer1': layer1_text,
                            'layer2': layer2_text,
                            'image': img,
                            'bytes': response.content
                        })
                    else:
                        st.error(f"❌ Failed to generate image for couple {idx+1}: {response.status_code}")
                        st.text(response.text)
                
                except Exception as e:
                    st.error(f"❌ Error generating image for couple {idx+1}: {str(e)}")
                
                progress_bar.progress((i + 1) / len(selected_indices))
            
            status_text.text("✅ Image generation complete!")
            progress_bar.empty()
            
            # Store in session state to persist after download
            st.session_state['generated_images'] = generated_images

# Display generated images from session state
if 'generated_images' in st.session_state and st.session_state['generated_images']:
    st.divider()
    st.subheader(f"📸 {len(st.session_state['generated_images'])} Images Generated")
    
    for i, img_data in enumerate(st.session_state['generated_images']):
        with st.container():
            st.markdown(f"""
            **Image {i+1}:**
            - **Header:** {img_data['layer1']}
            - **CTA:** {img_data['layer2']}
            """)
            
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.image(img_data['image'], width=400)
            
            with col2:
                st.download_button(
                    label="⬇️ Download",
                    data=img_data['bytes'],
                    file_name=f"template_{i+1}.png",
                    mime="image/png",
                    use_container_width=True,
                    key=f"download_{i}"
                )
            
            st.divider()


# Instructions
with st.expander("📖 How to Use"):
    st.markdown("""
    ### Step-by-step Guide:
    
    1. **Configure Template ID** in the sidebar
    
    2. **Enter Your Brief** and click "Generate 10 Header & CTA Variants"
       - The AI will create 10 different header and CTA button text combinations
    
    3. **Select the variants** you want to create images for
       - Check the boxes next to your favorite combinations
    
    4. **Click "Generate Images"** to create the final designs
       - Download individual images using the download buttons
    
    ### Example Values:
    - Template ID: `ab19c9f6-235a-4ee5-9397-16baa4f705a1`
    - Brief: `marketing for black friday`
    
    ### Notes:
    - The app automatically uses "header" and "cta" as layer IDs
    - API keys should be configured in Streamlit secrets:
      - `WRITER_API_KEY`
      - `PHOTOROOM_API_KEY`
    """)