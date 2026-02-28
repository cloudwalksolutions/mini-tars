package browser

import (
	"fmt"
	"os/exec"
)

// OpenVideoStreamChrome opens a new Chrome window and navigates to the video stream URL
func OpenVideoStreamChrome(url string) error {
	script := `
tell application "Google Chrome"
	make new window
	set the bounds of the front window to {0, 0, 660, 620} -- {left, top, right, bottom}
	set URL of (make new tab at end of tabs of front window) to "%s"
end tell
`
	return runAppleScript(fmt.Sprintf(script, url))
}

// CloseVideoStreamChrome closes the front window of Chrome
func CloseVideoStreamChrome() error {
	script := `
tell application "Google Chrome"
	close front window
end tell
`
	return runAppleScript(script)
}

// runAppleScript executes an AppleScript script
func runAppleScript(script string) error {
	cmd := exec.Command("osascript", "-e", script)
	return cmd.Run()
}
