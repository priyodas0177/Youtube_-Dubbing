def format_time(seconds):

    millis = int((seconds % 1) * 1000)

    hours = int(seconds // 3600)

    minutes = int((seconds % 3600) // 60)

    secs = int(seconds % 60)

    return f"{hours:02}:{minutes:02}:{secs:02},{millis:03}"



def create_srt(segments, texts, output_file):

    with open(output_file, "w", encoding="utf-8") as f:

        for i, (seg, text) in enumerate(zip(segments, texts), start=1):

            f.write(f"{i}\n")

            f.write(
                f"{format_time(seg['start'])} --> {format_time(seg['end'])}\n"
            )

            f.write(text.strip())

            f.write("\n\n")


    return output_file