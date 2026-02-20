# 🔐 Setting API Key in Railway

## ⚠️ IMPORTANT: API Key Security

**NEVER commit API keys to git or share them publicly!**

Since you've shared your API key, it's recommended to:
1. **Regenerate the key** in [Google AI Studio](https://aistudio.google.com/)
2. **Set it as an environment variable** in Railway (not in code)

---

## 🚀 How to Add API Key in Railway

### Step 1: Go to Railway Dashboard
1. Go to [railway.app](https://railway.app)
2. Sign in and select your project
3. Click on your service

### Step 2: Add Environment Variable
1. Click on the **"Variables"** tab
2. Click **"New Variable"** or **"Raw Editor"**
3. Add:
   ```
   GOOGLE_AI_API_KEY=AIzaSyCxejsLkePbsfHvNLgq39mJyVMYWbAwTOg
   ```

### Step 3: Save and Redeploy
1. Click **"Save"** or **"Update Variables"**
2. Railway will automatically redeploy with the new variable
3. Wait for deployment to complete

---

## 🔒 Security Best Practices

### ✅ DO:
- Set API keys as environment variables in Railway
- Use different keys for development and production
- Rotate keys regularly
- Keep keys secure and private

### ❌ DON'T:
- Commit API keys to git
- Share keys in chat/email
- Hardcode keys in source code
- Include keys in screenshots/documentation

---

## 🔄 Regenerating Your Key (Recommended)

Since this key was shared, consider regenerating it:

1. Go to [Google AI Studio](https://aistudio.google.com/)
2. Navigate to API Keys section
3. Delete or regenerate the old key
4. Create a new key
5. Update it in Railway environment variables

---

## ✅ Verify It's Working

After setting the environment variable:

1. Check Railway logs for: `Warning: GOOGLE_AI_API_KEY not set...`
   - If you DON'T see this warning, the key is set correctly ✅
   
2. Test the app:
   - Upload a resume
   - Check if it processes correctly

---

**Remember:** Your API key is now set securely in Railway and NOT in your code! 🔐

