# Image Generation Setup Guide

This guide explains how to set up Vertex AI Imagen 3 for product image generation.

## Prerequisites

1. **Google Cloud Project** with billing enabled
2. **Vertex AI API** enabled
3. **Service Account** with Vertex AI permissions
4. **Authentication** configured

## Step 1: Create Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing project
3. Note your **Project ID** (e.g., `wayfinder-supply-co`)

## Step 2: Enable Vertex AI API

1. In Google Cloud Console, go to **APIs & Services** > **Library**
2. Search for "Vertex AI API"
3. Click **Enable**

## Step 3: Create Service Account

1. Go to **IAM & Admin** > **Service Accounts**
2. Click **Create Service Account**
3. Name: `wayfinder-image-generator`
4. Grant role: **Vertex AI User** (`roles/aiplatform.user`)
5. Click **Done**

## Step 4: Create and Download Service Account Key

1. Click on the service account you just created
2. Go to **Keys** tab
3. Click **Add Key** > **Create new key**
4. Choose **JSON** format
5. Download the key file
6. Save it securely (e.g., `~/.config/gcp/wayfinder-key.json`)

## Step 5: Install Google Cloud SDK (if not already installed)

```bash
# macOS
brew install google-cloud-sdk

# Linux
curl https://sdk.cloud.google.com | bash
exec -l $SHELL

# Windows
# Download from https://cloud.google.com/sdk/docs/install
```

## Step 6: Authenticate

**Option A: Application Default Credentials (Recommended)**

```bash
# Set the environment variable
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/wayfinder-key.json"

# Or add to your shell profile (~/.bashrc, ~/.zshrc)
echo 'export GOOGLE_APPLICATION_CREDENTIALS="/path/to/wayfinder-key.json"' >> ~/.zshrc
source ~/.zshrc
```

**Option B: gcloud CLI**

```bash
gcloud auth activate-service-account --key-file=/path/to/wayfinder-key.json
gcloud config set project YOUR_PROJECT_ID
```

## Step 7: Set Environment Variables

```bash
export GOOGLE_CLOUD_PROJECT="your-project-id"
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/wayfinder-key.json"

# Optional: For Gemini text generation
export GOOGLE_API_KEY="your-gemini-api-key"
```

Or create a `.env` file:

```bash
GOOGLE_CLOUD_PROJECT=your-project-id
GOOGLE_APPLICATION_CREDENTIALS=/path/to/wayfinder-key.json
GOOGLE_API_KEY=your-gemini-api-key
```

## Step 8: Install Python Dependencies

```bash
pip install google-cloud-aiplatform google-generativeai
```

Or add to `scripts/requirements.txt`:

```
google-cloud-aiplatform>=1.38.0
google-generativeai>=0.3.0
```

## Step 9: Test Image Generation

```bash
# Test with a single product
python scripts/generate_products.py \
  --config config/product_generation.yaml \
  --skip-images false
```

## Troubleshooting

### Error: "Permission denied" or "403 Forbidden"

- Verify service account has `roles/aiplatform.user` role
- Check that Vertex AI API is enabled
- Verify `GOOGLE_APPLICATION_CREDENTIALS` points to correct key file

### Error: "Project not found"

- Verify `GOOGLE_CLOUD_PROJECT` matches your actual project ID
- Check project billing is enabled

### Error: "Imagen model not available"

- Imagen 3 may not be available in all regions
- Try setting region: `export GOOGLE_CLOUD_REGION="us-central1"`

### Error: "Quota exceeded"

- Check Vertex AI quotas in Google Cloud Console
- May need to request quota increase

## Alternative: Use OpenAI DALL-E 3

If Vertex AI is not available, you can use DALL-E 3:

1. Get OpenAI API key from https://platform.openai.com/api-keys
2. Set environment variable: `export OPENAI_API_KEY="your-key"`
3. Modify `config/product_generation.yaml`:
   ```yaml
   image_provider: "openai_dalle"
   ```
4. Update `scripts/generate_products.py` to use OpenAI API

## Alternative: Use Placeholder Images

For testing/development, use the placeholder image generator:

```bash
# Generate products first
python scripts/generate_sample_data.py

# Create placeholder images
pip install Pillow
python scripts/create_placeholder_images.py
```

## Cost Estimation

**Vertex AI Imagen 3 Pricing** (as of 2024):
- ~$0.02-0.04 per image
- 100 products = ~$2-4
- 1000 products = ~$20-40

**Recommendation**: Start with 10-20 products for testing, then scale up.

## Next Steps

Once images are generated:

1. Images will be saved to `public/images/products/`
2. Product JSON will reference image paths
3. Run `python scripts/seed_products.py` to index products
4. Verify images display in frontend


