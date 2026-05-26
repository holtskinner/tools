// Add this script to the Slide Deck
function portScriptToSpeakerNotes() {
  // 1. Replace with your specific Google Doc ID containing the script table
  var docId = "1f-YO4FvE5YTS94Vj_85bHYpSbOh-XgTUs8849XvfUe4"; 

  // Open the document and grab all tables
  var doc = DocumentApp.openById(docId);
  var body = doc.getBody();
  var tables = body.getTables(); 
  
  // Open the current presentation
  var presentation = SlidesApp.getActivePresentation();
  var slides = presentation.getSlides();

  var slideCounter = 0; // Cumulative counter for Option B sequential matching

  // Loop through all tables in the document
  for (var t = 0; t < tables.length; t++) {
    var table = tables[t];
    
    // Loop through the table rows (skipping the header row if it exists)
    var startRow = 2; // Change to 0 if you don't have a header row ("Script" | "Visual Notes")
    var numRows = table.getNumRows();
    
    for (var i = startRow; i < numRows; i++) {
      var row = table.getRow(i);
      
      // Extract text from the "Script" column (Column 1 / Index 0)
      var scriptText = row.getCell(0).getText().trim();
      
      // Extract the Slide URL or note from the "Visual" column (Column 2 / Index 1)
      var visualCell = row.getCell(1);
      var visualText = visualCell.getText();
      
      // Check if there is a specific hyperlink inside the Visual Notes column
      var slideUrl = null;
      var textObj = visualCell.getChild(0).asParagraph();
      
      // Look for a link inside the cell text
      if (textObj.getNumChildren() > 0) {
        for (var j = 0; j < textObj.getNumChildren(); j++) {
          var child = textObj.getChild(j);
          if (child.getType() == DocumentApp.ElementType.TEXT) {
            var linkUrl = child.getLinkUrl();
            if (linkUrl && linkUrl.includes("presentation/d/")) {
              slideUrl = linkUrl;
              break;
            }
          }
        }
      }
      
      // If no hyperlink found, look at the plain text for slide matches
      if (!slideUrl) {
        slideUrl = visualText;
      }

      // Match the row data to the correct slide in your deck
      if (scriptText.length > 0) {
        var targetSlide = null;
        
        // OPTION A: If your table explicitly links or names the slide index (e.g., "Slide 3")
        var slideIndexMatch = visualText.match(/Slide\s*(\d+)/i);
        if (slideIndexMatch) {
          var slideNum = parseInt(slideIndexMatch[1]) - 1; // Slides are 0-indexed in script
          if (slideNum < slides.length) {
            targetSlide = slides[slideNum];
          }
        } 
        
        // OPTION B: Fallback sequential matching cumulatively across tables
        if (!targetSlide) {
          if (slideCounter < slides.length) {
            targetSlide = slides[slideCounter];
          }
        }
        
        // Append the script text to the speaker notes of the identified slide
        if (targetSlide) {
          var notesPage = targetSlide.getNotesPage();
          var notesBody = notesPage.getSpeakerNotesShape().getText();
          // TODO: Remove
          notesBody.clear();
          // Append text (adds a new paragraph to existing notes)
          notesBody.appendText(scriptText + "\n\n");
          Logger.log("Ported script segment to Slide " + (slides.indexOf(targetSlide) + 1));
        }
        
        slideCounter++; // Increment the sequential index for the next valid script row
      }
    }
  }
}
