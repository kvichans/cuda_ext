Plugin for CudaText.
Adds lot of commands to the Commands dialog (not to Plugins menu, too much of them):

[Files]
  Open file by selected name
  Open file(s) in nearest right tab(s)...
  Open file(s) in nearest left tab(s)...
  Rename file...
  New file and SaveAs in current folder...
  Open all files from folder with sub-folders...

[Jumps]
  Navigate by error on console
  Jump to matching bracket
  Jump to next/previous changed/saved/working lines (6 commands)
  Jump to line with number in clipboard
  Scroll current line to screen center/top/bottom (3 commands)
  Scroll screen to left/right (2 commands)

[Editing]
  Add indented line above/below (2 commands)
  Align in lines by separator...
  Reindent selected lines... (it asks for old indent, for new indent, and changes indents of selected lines)
  Join selected lines
  Re-wrap/split lines by margin
  Fill selection by string...

[Paste]
  Paste to first column
  Paste with indent above
  Paste with indent below
  Paste like Lazarus IDE

[Find/Replace/Select]
  Find clipboard string: next
  Find clipboard string: previous
  Replace all occurences of selected string with clipboard value
  Copy word or [expression] or 'expression' without selection
  Replace word or [expression] or 'expression' with clipboard value
  Expand selection to word or "expression" or (expression)
  Expand and Copy selection to word or "expression" or (expression)
  Delete duplicate spaces
  Remove all ASCII chars 0..31 (except 9,10,13)

[File tabs]
  Activate previously active tab (go back)
  Activate tab #1..#9 in group #1 (9 commands)
  Activate tab #1..#9 in group #2 (9 commands)
  Activate last tab in group #1..#2 (2 commands)
  Activate next/prev tab (global loop) (2 commands)
  Move tab to position...
  Close active tab in next/previous group (2 commands)
  Switch tab to next/previous/first/last in next/previous group (8 commands)

[Splitters]
  Move splitter to expand/narrow side panel
  Move splitter to expand/narrow bottom panel
  Move splitter to expand/narrow top-left group
  Move splitter to expand/narrow active group

[Code Tree]
  Show current Code Tree path in statusbar
  Set active node of Code Tree, nearest to caret

[Paragraphs]
  Go to begin/end of paragraph (2 commands)
  Go to next/prev paragraph (2 commands)
  Align paragraphs: configure...
  Align paragraphs: left/right/center/fully justify (4 commands)
  

Author: Andrey Kvichanskiy (kvichans, at forum/github)
License: MIT
