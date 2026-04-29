# 🚀 Domain Email Intelligence Engine: Full System Walkthrough

This document covers the complete transformation of the engine into a state-of-the-art **DIY Hunter.io** alternative with a Cyberpunk aesthetic.

## 🟢 Phase 1: The "Hacker" Generator & Pro UI
We have completely redesigned the interface to feel like a high-security terminal, optimized for both client generation and administrative monitoring.

- **Client Generator (`/`)**: A Cyberpunk-themed "Hacker console" where users can trigger 1000-email data dumps. 
- **Admin Dashboard (`/admin`)**: A modern, high-density statistical monitoring portal with real-time stats and personnel search.
- **Consumption Logic**: Emails are now marked as `is_used` after generation, ensuring your client never receives duplicate data.

## 🔵 Phase 2: DIY Hunter.io (Intelligence Upgrade)
We have replicated premium features previously exclusive to third-party APIs (like Hunter.io), giving the system "Deep Intelligence" capabilities.

### 1. Deep SMTP Handshake
- **Standard Check**: Checks if the domain has a mail server.
- **Deep Handshake (New)**: Actually connects to the mail server and performs the `RCPT TO` handshake. It confirms the specific mailbox exists (e.g., `ceo@company.com`) without sending an email.
- **Result**: High-accuracy "Tier 2" verification for ultra-reliable leads.

### 2. Personnel Discovery & Synthesis
- **Name Scraper**: The crawler now identifies corporate "Team" and "About" pages and automatically extracts employee names (e.g., "John Doe").
- **Smart Synthesis**: The engine takes a discovered name and a domain's email pattern (e.g., `first.last`) to automatically generate and verify `john.doe@domain.com`.

### 3. Intelligence Search Tab
- **Location**: Found at `http://localhost:8000/admin` under the "Intelligence Search" tab.
- **Feature**: Deep query any domain in your database to instantly see its discovered patterns, staff members, and verified emails.

## ⚙️ System Controls (The Infinite Source)
- **Source**: Integrated **Common Crawl Web Graph**, giving the engine access to over **120 Million registered domains**.
- **Quotas**: Managed via the Admin Dashboard, you can set strict daily/monthly extraction limits. The system will automatically pause once a limit is reached and resume at the start of the next month.

---

## 🛠 How to Use
1. **Manage Limits**: Go to `/admin` and set your monthly limit (e.g., 50,000).
2. **Deep Query**: Use the "Intelligence Search" tab in the Admin panel to find staff for any domain.
3. **Generate for Client**: Go to the main homepage `/` and click **[ ⚡ GENERATE DATA ]** to dump a verified batch of 1,000 unique records.

> [!IMPORTANT]
> **Performance Tip**: When running at 50 threads, the engine is extremely fast. Ensure your PostgreSQL server has enough disk space to handle the millions of domain meta-records being streamed from Common Crawl.
