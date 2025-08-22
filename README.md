# MG-REXXS
A simple GUI tool for encrypting and decrypting `.xxs` video files from the Metal Gear Solid Master Collection.




## Features

* **Decrypt:** Converts `.xxs` files into a standard format (defaults to `.mp4`).
* **Encrypt:** Converts standard files (e.g., `.mp4`) back into the game's `.xxs` format.
* **Video Viewer:** Built-in video player that automatically loads MP4 files after conversion.


![xxs tool](<src="https://github.com/user-attachments/assets/938a5d8b-2f19-4d60-8ccf-898a88aff6e4" />
)


## How to Use

1.  Click the **"Browse..."** button to select your input file. This can be an encrypted `.xxs` file or a decrypted file (like `.mp4`).
2.  The tool will automatically determine the corresponding output filename and display it.
    For example:
    * If you selected `myvideo.xxs`, the output will be `myvideo.mp4`.
    * If you selected `myvideo.mp4`, the output will be `myvideo.xxs`.
3.  Click the **"Process File"** button.
4.  Once finished, the status bar will indicate success or show an error message. The output file will be saved in the same directory as the input file.
5.  If you converted an `.xxs` file to `.mp4`, the video will automatically load in the **Video Viewer** tab for immediate playback.

**Important Note:** The encryption/decryption key is generated based on the filename *without* the extension (e.g., `myvideo` from `myvideo.xxs`). Make sure your filenames match what the game expects. The tool uses the part of the filename *before the first dot* for seeding, which matches the original script's logic.
The tool will give you a pop up window warning you of this! I have also applied automatic naming conventions.

## How It Works

The tool uses the algorithm identified by user `eol`. It generates a unique pseudo-random number sequence using a specific Mersenne Twister algorithm variant. The seed for this generator is calculated based on the characters of the target filename (lowercase, without extension). The file data is then simply XORed with this number sequence to encrypt or decrypt it.

## Credits

* **Original `.xxs` Algorithm/Script:** eol
* **GUI Code:** 316austin316

## Known Bugs:
Apparently in the original script, there was a comment: "FURTHER WORK IS REQUIRED FOR FILE SIZE NOT A MULTIPLE OF 4" so perhaps this is still an issue, more tests need to be done!
