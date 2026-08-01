import os
import yt_dlp


def download_video(url, output_path, browser="chrome"):

    os.makedirs(
        os.path.dirname(output_path),
        exist_ok=True
    )


    ydl_opts = {

        # Same as successful terminal test
        "format": "bv*+ba/b",

        "merge_output_format": "mp4",

        "outtmpl": output_path,

        "quiet": False,


        # YouTube JS challenge solver
        "remote_components": [
            "ejs:github"
        ],


        # Browser login cookies
        "cookiesfrombrowser": (
            browser,
            None,
            None,
            None
        ),


        "extractor_args": {

            "youtube": {

                "player_client": [
                    "web",
                    "tv"
                ]

            }

        },


        "http_headers": {

            "User-Agent":
            (
                "Mozilla/5.0 "
                "(Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 "
                "(KHTML, like Gecko) "
                "Chrome/120 Safari/537.36"
            )

        },


        "retries": 10,

        "fragment_retries": 10,

    }



    with yt_dlp.YoutubeDL(ydl_opts) as ydl:

        ydl.extract_info(
            url,
            download=True
        )


    # safety check
    if not os.path.exists(output_path):
        raise Exception(
            "Video download failed"
        )


    return output_path