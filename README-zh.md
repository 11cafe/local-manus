# 🧠 Jaaz – AI自动化营销Agent助手 通用智能助手

一款本地桌面版的 Manus AI Agent 应用程序，支持一键安装到 Mac 和 Windows 电脑上。通用ai agent助手，擅长营销运营自动化。免费使用。

---

## 🚀 当前处于内测阶段 
如果你希望提前体验，请立即加入我们的内测名单：[https://tally.so/r/nPgeKQ](https://tally.so/r/nPgeKQ)，我们将发送你下载链接体验！你的反馈将有助于塑造 Jaaz 的未来方向并加快其正式发布。


---

## ✨ 核心功能

### **🤖 内置 AI 营销内容写作助手**

- 智能自动补全 & 编辑建议
- 只需提供一张图片或视频，即可生成整篇内容

### **🔁 一键跨平台发布**

- AI 自动调整内容风格和格式以适配不同平台
- 支持一次发布到多个平台（如 小红书、抖音、B站、微信视频号、Youtube等）
- 可追踪所有帖子的表现并查看分析数据

### **💬 AI “ReplyGuy” 自动回复助手**

- 自动寻找适合提及你产品的帖子（如 Reddit 等）
- 生成自然融入对话的产品推荐回复
- 可选择在提交前让你确认内容（可关闭）

### **🖼️ \[即将上线] 图像与视频增强功能**

- 添加 TikTok/CapCut 风格的文字特效
- 自动生成插图式图像用于内容创作

<img width="900" alt="Screenshot 2025-05-11 at 11 28 29 PM" src="https://github.com/user-attachments/assets/739cb0ca-d197-40d9-a0f7-2328b26d210c" />

---

- 支持 **macOS** 和 **Windows**
- 可自由选择 AI 模型：接入 Claude、OpenAI、Gemini API，或使用 [Ollama](https://github.com/ollama/ollama) 实现**完全免费**的本地运行




---

## 📦 Manus AI Agent — 最会帮你推广营销、浏览器自动化执行的本地 Agent！

**本地 Agent 的最大优势在于它可以共享你本地浏览器的登录状态**，让 Agent 能够登录任意网站并执行任务。许多网站（如小红书、抖音等）都需要登录才能进行搜索或发布内容，而云上的 Agent 则无法访问这些数据或执行社交平台的相关操作。

Manus 深度集成了浏览器自动化、文件读写、代码运行、图像与视频编辑等多项功能。它最擅长的就是操作浏览器，让 AI 不只是告诉你怎么做，而是直接帮你完成任务！

---

## 🔒 安全机制

- 所有敏感操作（如登录、发帖、回帖）均可设置为必须手动确认
- 可仅使用专用营销账号登录，避免涉及个人敏感信息或支付方式
- 所有 AI 行为都会被记录为文本+截图，便于随时审查风险
- 未来计划：增加智能防护系统，自动检测并阻止潜在风险行为

---

## 📷 截图展示

#### ✨ 一键跨平台发布：图文视频一齐搞定！

<img width="700" alt="cross-posting-dropdown" src="https://github.com/user-attachments/assets/c03367a3-0515-49ae-97be-cb470c3d3e78" />

#### ✍️ AI 内容编辑器：自动补全文案

<img width="700" alt="auto-complete" src="https://github.com/user-attachments/assets/bed9858d-20d5-40c0-b580-9b9236414663" />

#### 🌐 AI 会引导你登录账号：只需打开浏览器完成常规登录即可

<img width="700" alt="Screenshot 2025-05-11 at 10 53 19 PM" src="https://github.com/user-attachments/assets/ca6052e5-9522-4a69-b73e-8806404071cd" />

例如，在 AI 提示中点击“open browser”链接，就会自动打开 Instagram 登录页面，正常登录后即可保存状态：

<img width="400" alt="Screenshot 2025-05-11 at 11 59 24 PM" src="https://github.com/user-attachments/assets/b6395a86-3d5c-4432-8435-564f04388aec" />

#### 💬 AI “ReplyGuy” - 自动搜索相关帖子并帮你自然植入产品信息

你可以从 AI 推荐的帖子中选择要回复的内容：

<img width="700" alt="replyguy" src="https://github.com/user-attachments/assets/d03482b1-3d6c-423a-a193-e1eeb96923e7" />

AI 还可以让你在提交回复前进行确认：

<img width="500" alt="replyguy-confirm-reply-content" src="https://github.com/user-attachments/assets/7371dc11-e3fd-4966-88b0-73070fbbd1be" />

---

## 开发指南

```bash
cd react && npm i
cd react && npm run dev
cd server && uvicorn main:app --host "0.0.0.0" --reload
```

---
