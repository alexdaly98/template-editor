import streamlit as st
import requests
from writerai import Writer
from io import BytesIO
from PIL import Image

st.set_page_config(page_title="AI Template Editor", layout="wide")

st.title("🎨 AI-Powered Template Editor")

# Sidebar for API keys and configuration
with st.sidebar:
    st.header("⚙️ Configuration")
    writer_api_key = st.text_input("Writer API Key", type="password")
    photoroom_api_key = st.text_input("PhotoRoom API Key", type="password")
    
    st.divider()
    
    template_id = st.text_input("Template ID", value="ab19c9f6-235a-4ee5-9397-16baa4f705a1")
    layer_id = st.text_input("Layer ID", value="header")

# Main content
st.header("📝 Step 1: Generate Title Variants")

brief = st.text_area(
    "Marketing Brief",
    value="marketing for black friday",
    help="Describe what kind of titles you want to generate"
)

if st.button("🚀 Generate 10 Variants", type="primary", use_container_width=True):
    if not writer_api_key:
        st.error("❌ Please enter your Writer API key in the sidebar")
    else:
        with st.spinner("Generating title variants..."):
            try:
                # Initialize Writer client
                client = Writer(api_key=writer_api_key)
                
                # Generate variants
                completion = client.completions.create(
                    model="palmyra-x-003-instruct",
                    prompt=f"Generate 10 different catchy title variants for {brief}. Make them short, punchy, and effective for marketing. Return only the titles, one per line, numbered 1-10.",
                    max_tokens=500
                )
                
                # Parse variants
                text = completion.choices[0].text
                lines = [line.strip() for line in text.split('\n') if line.strip()]
                variants = [line.split('.', 1)[-1].strip() if '.' in line else line for line in lines]
                variants = [v.split(')', 1)[-1].strip() if ')' in v else v for v in variants]
                variants = variants[:10]  # Ensure we have exactly 10
                
                # Store in session state
                st.session_state['variants'] = variants
                st.session_state['selected_variants'] = []
                
                st.success(f"✅ Generated {len(variants)} title variants!")
                
            except Exception as e:
                st.error(f"❌ Error generating variants: {str(e)}")

# Display variants if they exist
if 'variants' in st.session_state and st.session_state['variants']:
    st.divider()
    st.header("✅ Step 2: Select Variants to Generate Images")
    
    # Create checkboxes for each variant
    selected_indices = []
    
    cols = st.columns(2)
    for idx, variant in enumerate(st.session_state['variants']):
        col = cols[idx % 2]
        with col:
            if st.checkbox(f"**{idx + 1}.** {variant}", key=f"var_{idx}"):
                selected_indices.append(idx)
    
    st.session_state['selected_variants'] = selected_indices
    
    # Generate images button
    st.divider()
    if st.button("🖼️ Generate Images for Selected Variants", type="primary", use_container_width=True):
        if not photoroom_api_key:
            st.error("❌ Please enter your PhotoRoom API key in the sidebar")
        elif not template_id or not layer_id:
            st.error("❌ Please enter Template ID and Layer ID in the sidebar")
        elif len(selected_indices) == 0:
            st.warning("⚠️ Please select at least one variant")
        else:
            st.header("🎨 Generated Images")
            
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            generated_images = []
            
            for i, idx in enumerate(selected_indices):
                variant_text = st.session_state['variants'][idx]
                status_text.text(f"Generating image {i+1}/{len(selected_indices)}: {variant_text[:50]}...")
                
                try:
                    # Prepare form data
                    form_data = {
                        "templateId": (None, template_id),
                        f"layers.{layer_id}.text.content": (None, variant_text)
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
                            'title': variant_text,
                            'image': img,
                            'bytes': response.content
                        })
                    else:
                        st.error(f"❌ Failed to generate image for variant {idx+1}: {response.status_code}")
                        st.text(response.text)
                
                except Exception as e:
                    st.error(f"❌ Error generating image for variant {idx+1}: {str(e)}")
                
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
            st.markdown(f"**{i+1}. {img_data['title']}**")
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
    
    1. **Enter API Keys** in the sidebar:
       - Writer API key for text generation
       - PhotoRoom API key for image generation
    
    2. **Configure Template Settings** in the sidebar:
       - Template ID (the PhotoRoom template to use)
       - Layer ID (the text layer to modify)
    
    3. **Enter Your Brief** and click "Generate 10 Variants"
       - The AI will create 10 different title options
    
    4. **Select the variants** you want to create images for
       - Check the boxes next to your favorite titles
    
    5. **Click "Generate Images"** to create the final designs
       - Download individual images using the download buttons
    
    ### Example Values:
    - Template ID: `ab19c9f6-235a-4ee5-9397-16baa4f705a1`
    - Layer ID: `header`
    - Brief: `marketing for black friday`
    """)