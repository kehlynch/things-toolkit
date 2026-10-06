on run argv
    tell application "/Applications/Things3.app"
        set targetArea to area id (item 1 of argv)
        if name of targetArea is not (item 2 of argv) then error "Area name changed; review again"
        if exists (areas whose name is (item 3 of argv)) then error "Destination name already exists"
        set name of targetArea to item 3 of argv
        if name of targetArea is not (item 3 of argv) then error "Rename verification failed"
        return id of targetArea
    end tell
end run
