# 🧠 LocalManus – Your AI Marketing Agent & Copilot

Meet **Jaaz**, your all-in-one AI-powered marketing assistant. A fully **local** **desktop app** that runs for **free** — no cloud lock-in, no monthly fees. Think of it as the "Cursor" for marketers and content creators: an always-on team that helps you 10x your productivity and supercharge product growth 📈


---

[中文](https://github.com/11cafe/local-manus/blob/main/README-zh.md)

## ✨ Key Features

**🤖 AI Marketing Content Copilot in Editor**

* Smart auto-complete & edit suggestions, generate entire posts from a **single image or video**

**🔁 1-Click Cross-Posting**

* Publish to multiple platforms at once (e.g., Twitter, Medium, LinkedIn), supports ***almost any site*** by AI browser automation
* AI smartly adapts and optimizes your content to match each platform’s tone, format
* Track performance and view analytics across posts

**💬 AI “ReplyGuy”**

* Automatically find best places to mention your product, like Reddit posts, etc.
* Generate & post replies that **naturally mention your product**
* Prompting you to review before submitting (optional, can turn off)

**🖼️ \[Upcoming] Image & Video Enhancements**

* Add stylized text overlays (like you see on Tiktok/CapCut)
* Auto-generate illustrative images for your content


<img width="900" alt="Screenshot 2025-05-11 at 11 28 29 PM" src="https://github.com/user-attachments/assets/739cb0ca-d197-40d9-a0f7-2328b26d210c" />

---

* Available for **macOS** and **Windows**
* Bring your own AI: use Claude, OpenAI, Gemini via API key, or run locally with [Ollama](https://github.com/ollama/ollama) for **100% free** usage

---

## Security

* **You can choose to require sensitive actions always require your confirmation**: logins, posts, replies, etc.
* You can choose to only sign-in dedicated marketing accounts that doesn't contain any sensitive info – no access to personal data or credit cards
* All actions taken by AI are strictly recorded in history, as both text and screenshot images. You can manually search the records to identify any security risks
* Future plan: add a smart safeguard system to detect and block risky behavior

## Screenshots

#### ✨1Click Cross Posting marketing content to multiple platforms, image, text, video supported!

<img width="700" alt="cross-posting-dropdown" src="https://github.com/user-attachments/assets/c03367a3-0515-49ae-97be-cb470c3d3e78" />



#### ✍️AI powered content editor, auto complete your writing

<img width="700" alt="auto-complete" src="https://github.com/user-attachments/assets/bed9858d-20d5-40c0-b580-9b9236414663" />


#### 🌐AI will prompt you to login to your account, simply by opening the browser and do a regular login to the website you want to post to. You only need to do this once since it will remember you

<img width="700" alt="Screenshot 2025-05-11 at 10 53 19 PM" src="https://github.com/user-attachments/assets/ca6052e5-9522-4a69-b73e-8806404071cd" />


For exmple, click in "open browser" link in AI's prompt message will open up the login page of Instagram, do your normal login there and it will remember you

<img width="400" alt="Screenshot 2025-05-11 at 11 59 24 PM" src="https://github.com/user-attachments/assets/b6395a86-3d5c-4432-8435-564f04388aec" />

#### AI "replyguy" - automatic find relevant posts about your product area, generate replies to mention your product naturally under the post, like Replyguy.com (but Free!)

You can choose which post to reply to, simply by clicking AI provided options:

<img width="700" alt="replyguy" src="https://github.com/user-attachments/assets/d03482b1-3d6c-423a-a193-e1eeb96923e7" />

And it can ask you to review the reply content before submitting the reply:

<img width="500" alt="replyguy-confirm-reply-content" src="https://github.com/user-attachments/assets/7371dc11-e3fd-4966-88b0-73070fbbd1be" />



## Development

`cd react && npm i`
`cd react && npm run dev`
`cd server && python main.py`
