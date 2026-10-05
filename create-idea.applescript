-- Explicitly invoked creation only. Arguments are data, never interpolated code.
on run argv
    if (count of argv) is not 2 then error "Expected title and notes"
    set itemTitle to item 1 of argv
    set itemNotes to item 2 of argv
    tell application "/Applications/Things3.app"
        if exists (to dos whose name is itemTitle) then error "Title already exists; inspect before retrying"
        set newItem to make new to do with properties {name:itemTitle, notes:itemNotes} at beginning of list "Someday"
        if name of newItem is not itemTitle then error "Title verification failed"
        if notes of newItem is not itemNotes then error "Notes verification failed"
        return id of newItem
    end tell
end run
