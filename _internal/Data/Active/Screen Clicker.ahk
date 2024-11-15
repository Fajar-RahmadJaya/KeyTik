; text
^!p::
ExitApp

#Persistent
SetTimer, CheckImages, 500  ; Set an interval of 500 ms (0.5 seconds)
return

; Define the paths for each image here for easy modification
imagePath1 := "C:\path\to\your\images.png"
imagePath2 := "C:\path\to\your\images.png"
imagePath3 := "C:\path\to\your\images.png"
imagePath4 := "C:\path\to\your\images.png"

CheckImages:
    ; Look for 1.png and click it if found
    if (ImageSearchClick(imagePath1))
    {
        Sleep, 1000  ; Wait for 1 second (adjust as needed)
        
        ; After clicking 1.png, try to find 2.png and click it
        ImageSearchClick(imagePath2)
        
        ; Check if 3.png is present
        if (ImageSearch(imagePath3))
        {
            ; If 3.png is found, click 4.png
            ImageSearchClick(imagePath4)
        }
        ; Otherwise, do nothing and wait for the next interval
    }
return

; Function to locate and click an image if it exists
ImageSearchClick(imagePath)
{
    CoordMode, Pixel, Screen  ; Search the entire screen
    ImageSearch, X, Y, 0, 0, A_ScreenWidth, A_ScreenHeight, %imagePath%
    if !ErrorLevel
    {
        Click, %X%, %Y%  ; Click on the found image
        return true
    }
    return false
}

; Function to only search for an image (without clicking)
ImageSearch(imagePath)
{
    CoordMode, Pixel, Screen
    ImageSearch, X, Y, 0, 0, A_ScreenWidth, A_ScreenHeight, %imagePath%
    return !ErrorLevel
}
