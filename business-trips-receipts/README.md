# Business Trip Square Receipt Auto-Forwarder ✈️🧾

This automation runs directly inside **Google Apps Script** (the cloud automation platform built into your Google Account). It is completely free, secure, and runs automatically once daily.

## How It Works

1. **Checks Today's Calendar:** Once daily, the script checks if you are currently on business travel by searching your primary Google Calendar for an event (either an all-day or timed event) starting with **"Business travel"** (case-insensitive).
   - If no matching event exists for today, the script exits immediately without scanning Gmail.
2. **Finds Unprocessed Square Receipts:** If you are on business travel today, it searches your Gmail for new, unprocessed receipts from `messenger@messaging.squareup.com` received within the **last month (30 days)**.
3. **Double-Layered Duplicate Protection:**
   - **Gmail Filter Check:** The query explicitly excludes any threads containing emails sent to `receipts@concur.com` (`-to:receipts@concur.com`).
   - **Header Header Verification:** Even if conversation threading differs, the script inspects individual message recipient fields (`To`, `Cc`, `Bcc`). If any email in the thread shows it was already forwarded to `receipts@concur.com`, it skips forwarding and marks the thread as processed.
4. **Verifies Receipt Date Matching:** 
   - For each receipt, it checks if its receipt date also has a matching **"Business travel"** calendar event.
   - If the receipt date falls on a travel day, it is forwarded to `receipts@concur.com`.
   - If the receipt date does not fall on a travel day, it skips forwarding.
5. **Marks as Processed:** To ensure every email is evaluated exactly once and to prevent duplicate checks, the script applies a `Concur/Forwarded` label to processed threads.

---

## Quick Setup (No CLI Required)

The easiest way to set up this automation is using the Google Apps Script web editor:

1. **Open Google Apps Script:**
   Go to [script.google.com](https://script.google.com) and sign in with the Google Account associated with your Gmail and Calendar.

2. **Create a New Project:**
   Click the **"New Project"** button in the top-left corner.

3. **Paste the Code:**
   - Delete any default code in the editor (`myFunction` skeleton).
   - Open [Code.gs](./Code.gs) in this directory, copy its entire contents, and paste it into the online editor.
   - Click the Save icon (floppy disk) or press `Ctrl+S` / `Cmd+S`.

4. **Change Configuration (Optional):**
   Customize variables at the top of the script if needed (e.g. `DESTINATION_EMAIL`, `TRAVEL_EVENT_PREFIX`, etc.).

---

## Test Your Script

1. **Select Function:**
   In the toolbar at the top of the editor, select `autoForwardSquareReceipts` from the dropdown list next to "Debug".

2. **Create a Test Event:**
   In your Google Calendar, create an **all-day event** or **timed event** for **today** with the title starting with **"Business travel"** (e.g., "Business travel to NYC").

3. **Verify with a Test Email:**
   If you have a recent email from `messenger@messaging.squareup.com` that arrived today:
   - Ensure it does **not** have the `Concur/Forwarded` label.
   - Run the script by clicking the **"Run"** button in the toolbar.
   - If it's your first run, click **Review Permissions** and grant access to your Gmail and Calendar.
   - The script will find the email, see that today is a "Business travel" day, match the receipt's date, and forward it.

---

## Automate It (Set Up a Daily Trigger)

To run this script automatically once daily:

1. In the Apps Script editor, click the **Triggers** icon (the clock icon `⏰` on the left sidebar).
2. Click **"+ Add Trigger"** in the bottom-right corner.
3. Configure the trigger as follows:
   - **Choose which function to run:** `autoForwardSquareReceipts`
   - **Choose which deployment should run:** `Head`
   - **Select event source:** `Time-driven`
   - **Select type of time-based trigger:** `Day timer`
   - **Select time of day:** `10pm to 11pm` or `11pm to Midnight` (highly recommended to capture all receipts that came in during that day)
4. Click **Save**.

Now, the automation will run silently once every night in the cloud, processing and forwarding any Square receipts received that day if you are traveling!

---

## Advanced CLI Setup (Using `clasp`)

If you prefer to manage and deploy your script using the command line:

1. Install `clasp` globally:
   ```bash
   npm install -g @google/clasp
   ```
2. Log in to your Google Account:
   ```bash
   clasp login
   ```
3. Create/Clone your Apps Script project inside this folder:
   ```bash
   clasp create --title "Business Trip Square Receipt Forwarder" --type standalone
   ```
4. Push the files to the cloud:
   ```bash
   clasp push
   ```
5. Open the project in your browser to configure triggers:
   ```bash
   clasp open
   ```
