// =========================================================================
// GOOGLE APPS SCRIPT: AUTO-FORWARD SQUARE RECEIPTS TO CONCUR DURING TRIPS
// =========================================================================
//
// Description:
// This script runs automatically once daily on a Google Apps Script trigger.
// It checks if you have an active calendar event (either all-day or timed)
// on your primary calendar starting with the title "Business travel" for today.
//
// If you are on business travel today:
// 1. It searches Gmail for unprocessed Square receipts received within the last month (30 days).
// 2. It automatically filters out and ignores any threads that have already been
//    forwarded to receipts@concur.com (using both Gmail search filters and message headers).
// 3. For each receipt, it verifies that its arrival date falls within any of
//    your "Business travel" periods.
// 4. It forwards matching receipts to receipts@concur.com and labels them.
//
// Setup instructions are detailed in the accompanying README.md file.
// =========================================================================

// ==================== CONFIGURATION ====================
// Destination email address (Concur receipts inbox)
const DESTINATION_EMAIL = 'receipts@concur.com';

// Correct Square messaging email address
const SQUARE_SENDER = 'messenger@messaging.squareup.com';

// Gmail search query to identify Square receipts
const GMAIL_SEARCH_QUERY = `from:${SQUARE_SENDER} subject:("Receipt from" OR "Your receipt" OR "Receipt")`;

// Label name used to mark emails that have already been processed
const PROCESSED_LABEL_NAME = 'Concur/Forwarded';

// Prefix to look for in calendar event titles to identify business travel
const TRAVEL_EVENT_PREFIX = 'business travel';
// =======================================================

/**
 * Main function to run the automation daily.
 * Set this up to run on a daily time-driven trigger (e.g., every evening between 10pm-11pm).
 */
function autoForwardSquareReceipts() {
  Logger.log('Starting daily Square receipt forwarding automation...');
  
  const today = new Date();
  
  // 1. Verify if we are currently on business travel today
  if (!hasBusinessTravelForDate(today)) {
    Logger.log('Today is not a business travel day. Skipping receipt forwarding.');
    return;
  }
  
  Logger.log('On business travel today! Processing receipts...');
  
  // 2. Ensure the processed label exists
  const label = getOrCreateLabel(PROCESSED_LABEL_NAME);
  
  // 3. Search for unprocessed Square receipts from the last month (30 days ago)
  const thirtyDaysAgo = new Date();
  thirtyDaysAgo.setDate(thirtyDaysAgo.getDate() - 30);
  
  let timeZone = "GMT";
  try {
    timeZone = Session.getScriptTimeZone();
  } catch (e) {
    Logger.log(`Warning: Could not fetch script timezone, defaulting to GMT. Error: ${e.toString()}`);
  }
  const formattedDate = Utilities.formatDate(thirtyDaysAgo, timeZone, "yyyy/MM/dd");
  
  // Exclude threads already containing messages sent to DESTINATION_EMAIL
  const searchQuery = `${GMAIL_SEARCH_QUERY} -label:${PROCESSED_LABEL_NAME} -to:${DESTINATION_EMAIL} after:${formattedDate}`;
  Logger.log(`Searching Gmail with query: ${searchQuery}`);
  
  const threads = GmailApp.search(searchQuery);
  Logger.log(`Found ${threads.length} unprocessed thread(s) matching query from the last 30 days.`);
  
  let forwardCount = 0;
  
  for (const thread of threads) {
    const messages = thread.getMessages();
    
    // Double-check recipient headers to ensure the receipt hasn't been forwarded
    let alreadyForwarded = false;
    for (const msg of messages) {
      const toField = msg.getTo().toLowerCase();
      const ccField = msg.getCc().toLowerCase();
      const bccField = msg.getBcc().toLowerCase();
      
      if (toField.includes(DESTINATION_EMAIL.toLowerCase()) || 
          ccField.includes(DESTINATION_EMAIL.toLowerCase()) || 
          bccField.includes(DESTINATION_EMAIL.toLowerCase())) {
        alreadyForwarded = true;
        break;
      }
    }
    
    if (alreadyForwarded) {
      Logger.log(`Skipped: Thread was already forwarded to ${DESTINATION_EMAIL} (detected via message recipient headers). Labeling as processed.`);
      thread.addLabel(label);
      continue;
    }
    
    let threadNeedsLabeling = false;
    
    for (const message of messages) {
      const messageDate = message.getDate();
      Logger.log(`Checking receipt from ${messageDate.toDateString()} with subject "${message.getSubject()}"...`);
      
      // 4. Verify if the receipt's arrival date was also during a business travel period
      if (hasBusinessTravelForDate(messageDate)) {
        Logger.log(`MATCH! Receipt date ${messageDate.toDateString()} is a business travel day.`);
        
        try {
          Logger.log(`Forwarding message to ${DESTINATION_EMAIL}...`);
          message.forward(DESTINATION_EMAIL);
          forwardCount++;
          threadNeedsLabeling = true;
        } catch (e) {
          Logger.log(`Error forwarding message: ${e.toString()}`);
        }
      } else {
        Logger.log(`Skipped: Receipt date ${messageDate.toDateString()} was not during a business travel period.`);
        threadNeedsLabeling = true; // Mark as processed so we don't scan it again on future trips
      }
    }
    
    // Label the thread as processed so we don't scan it on future runs
    if (threadNeedsLabeling) {
      thread.addLabel(label);
    }
  }
  
  Logger.log(`Finished execution. Successfully forwarded ${forwardCount} receipt(s).`);
}

/**
 * Checks if a given date has an active event (all-day or timed) on the primary calendar
 * whose title starts with "Business travel" (case-insensitive) and includes the given date.
 * @param {Date} date The date to check.
 * @return {boolean} True if the date is a business travel day, false otherwise.
 */
function hasBusinessTravelForDate(date) {
  const calendar = CalendarApp.getDefaultCalendar();
  if (!calendar) {
    Logger.log('Could not find primary calendar.');
    return false;
  }
  
  // Normalize checking date to midnight
  const targetDay = new Date(date.getFullYear(), date.getMonth(), date.getDate());
  
  // Query calendar events from 1 day before to 1 day after to handle all overlaps
  const oneDayMs = 24 * 60 * 60 * 1000;
  const searchStart = new Date(targetDay.getTime() - oneDayMs);
  const searchEnd = new Date(targetDay.getTime() + 2 * oneDayMs);
  
  const events = calendar.getEvents(searchStart, searchEnd);
  
  for (const event of events) {
    const title = event.getTitle().toLowerCase();
    
    // Check if the event title starts with "Business travel"
    if (title.startsWith(TRAVEL_EVENT_PREFIX.toLowerCase())) {
      const eventStart = event.getStartTime();
      const eventEnd = event.getEndTime();
      
      // Normalize event start day to midnight
      const startDay = new Date(eventStart.getFullYear(), eventStart.getMonth(), eventStart.getDate());
      
      // Adjust end day: if the event ends exactly at 12:00 AM (midnight), the previous day is the last active travel day
      let adjustedEventEnd = eventEnd;
      if (eventEnd.getHours() === 0 && eventEnd.getMinutes() === 0 && eventEnd.getSeconds() === 0) {
        adjustedEventEnd = new Date(eventEnd.getTime() - 1000);
      }
      const endDay = new Date(adjustedEventEnd.getFullYear(), adjustedEventEnd.getMonth(), adjustedEventEnd.getDate());
      
      // Check if targetDay is between startDay and endDay (inclusive)
      if (targetDay >= startDay && targetDay <= endDay) {
        Logger.log(`Active business travel detected on ${targetDay.toDateString()} from event "${event.getTitle()}" (${eventStart.toString()} to ${eventEnd.toString()})`);
        return true;
      }
    }
  }
  
  return false;
}

/**
 * Gets a Gmail label by name, creating it if it doesn't exist.
 * @param {string} name Name of the label (supports nested labels like "Parent/Child").
 * @return {GmailLabel} The Gmail label.
 */
function getOrCreateLabel(name) {
  let label = GmailApp.getUserLabelByName(name);
  if (!label) {
    Logger.log(`Creating label "${name}"`);
    label = GmailApp.createLabel(name);
  }
  return label;
}
