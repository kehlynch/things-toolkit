on run argv
    tell application "/Applications/Things3.app"
        set theItem to to do id (item 1 of argv)
        set destination to list id (item 2 of argv)
        if name of theItem is not (item 3 of argv) then error "Title changed"
        if notes of theItem is not (item 4 of argv) then error "Notes changed"
        move theItem to destination
        if (id of every to do of destination) does not contain (item 1 of argv) then error "Move verification failed"
        return "verified"
    end tell
end run
