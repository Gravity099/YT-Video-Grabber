from tkinter import *
import customtkinter as c
from pytubefix import YouTube
from pytubefix.exceptions import RegexMatchError, VideoUnavailable
import urllib.error , urllib.request
import os
import requests
import random
import string
from PIL import Image , ImageFilter, ImageTk
from tkinter import filedialog , messagebox
import warnings
import threading
import queue
import time 
import logging
import sys 
import ssl
import certifi


def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)

# Format seconds into HH:MM:SS or MM:SS
def format_length(seconds):
    hours, remainder = divmod(seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    if hours > 0:
        return f"{hours:02}:{minutes:02}:{seconds:02}"  
    else:
        return f"{minutes:02}:{seconds:02}"

# Format views with K, M, B depending upon the views retrive 
def format_views(views):
    if views >= 1_000_000_000:
        return f"{views / 1_000_000_000:.1f}B"  
    elif views >= 1_000_000:
        return f"{views / 1_000_000:.1f}M"  
    elif views >= 1_000:
        return f"{views / 1_000:.1f}K"  
    else:
        return str(views)



def check_url():
    """
    Here, The Application starts calling the other Function after checking 
    the exception being input by the url 
    such as  InputError , UrlVerication , InternetConnectivity 
    """
    url = my_entry.get()
    if not url.strip():
        messagebox.showerror(title="InputError",message="Paste the Youtube URL")
        logging.info("Paste the Url")
        return
    else:
        try:
            ssl_context = ssl.create_default_context(cafile=certifi.where())
            response = urllib.request.build_opener(urllib.request.HTTPSHandler(context=ssl_context))
            urllib.request.install_opener(response)
            yt = YouTube(url)
            simple_title.configure(text=yt.title)
            channel_label.configure(text=f"Channel Name : {yt.author}")
            calc_duration = format_length(yt.length)
            calc_views = format_views(yt.views)
            duration_label.configure(text=f"Duration : {calc_duration}")
            views_label.configure(text=f"Views : {calc_views}")
            logging.info(f"URLInput : {url}")
            # Calling other necessary function 
            download_thumb(url)
            setting_widgets()
            global attr         # Access later 
            attr = None
        except (RegexMatchError,VideoUnavailable):              # Verifying the correct Url 
            messagebox.showerror(title="URLVerificationError",message="Invalid Url")
            logging.error("Invalid URL")
            return
        except urllib.error.URLError:                           # Internet Connected to proceed Further
            messagebox.showerror(title="NetworkError",message="Internet Not Connected")
            logging.error("NetworkError : Internet not Connected")
            return         
        except Exception as e:                                  # Changes the Youtube Data Api 
            messagebox.showerror(title="BadRequest",message=f"Software need the Update \n Request Sent \n{e} ")
            return
            

def download_thumb(thumb):
    """
    Download the thumbnail, using PIL to resize it and 
    display it in the tkinter window.
    """
    try:
        dropdown(thumb)
        thumb_video = YouTube(thumb)
        thumbnail_url = thumb_video.thumbnail_url

        thumbnail_dir = os.path.join(resource_path("."), "Thumbnail")
        os.makedirs(thumbnail_dir, exist_ok=True)

        # Download the thumbnail
        response = requests.get(thumbnail_url)
        if response.status_code == 200:
            random_name = ''.join(random.choices(string.ascii_letters + string.digits, k=8)) + ".png"
            save_path = os.path.join(thumbnail_dir, random_name)

            # Save the thumbnail
            with open(save_path, "wb") as f:
                f.write(response.content)

            # Load, crop, and resize the thumbnail
            image_path = os.path.join(thumbnail_dir, random_name)  # Use os.path.join for correct path
            with Image.open(image_path) as img:
                img = img.convert("RGB")

                # Remove black bars by cropping top and bottom
                top_crop, bottom_crop = 0, 0
                for y in range(img.height):
                    row = img.crop((0, y, img.width, y + 1)).getcolors(img.width)
                    if row and all(color[1] == (0, 0, 0) for color in row):
                        top_crop += 1
                    else:
                        break

                for y in range(img.height - 1, -1, -1):
                    row = img.crop((0, y, img.width, y + 1)).getcolors(img.width)
                    if row and all(color[1] == (0, 0, 0) for color in row):
                        bottom_crop += 1
                    else:
                        break

                # Crop and save the processed image
                crop_box = (0, top_crop, img.width, img.height - bottom_crop)
                cropped_image = img.crop(crop_box)

                new_size = (230, 140)
                resized_image = cropped_image.resize(new_size, Image.LANCZOS)
                sharpened_image = resized_image.filter(ImageFilter.SHARPEN)

                save_dir = os.path.join(resource_path("."), "Saved pics")
                os.makedirs(save_dir, exist_ok=True)
                save_name = ''.join(random.choices(string.ascii_letters + string.digits, k=8)) + ".png"
                final_save_path = os.path.join(save_dir, save_name)
                sharpened_image.save(final_save_path)

                # Display the final image in the tkinter window
                t_image = ImageTk.PhotoImage(Image.open(final_save_path))
                image_label.configure(image=t_image)
                image_label.image = t_image  # Reference to avoid garbage collection
        else:
            notfound_image = resource_path("Mandatory/notfound.png")
            fallback_image = PhotoImage(file=notfound_image)
            image_label.configure(image=fallback_image)
            image_label.image = fallback_image  # Reference to avoid garbage collection
    except Exception as e:
        logging.error(f"Thumbnail could not be downloaded or processed: {e}")
        pass

def dropdown(url3):
    """
    Fetch that avialble downloading streams from pytubefi x library and 
    show in the drop down menu for user preference
    """
    yt = YouTube(url3)

    video_streams = yt.streams.filter(progressive=False, file_extension='mp4').order_by('resolution').desc()

    video_streams = yt.streams.filter(progressive=False, file_extension='mp4').order_by('resolution').desc()

    # Create a list to store video resolutions, file sizes, and file extension
    video_info = []
    seen_resolutions = set()  # Track seen resolutions

    for stream in video_streams:  
        if len(video_info) >= 2:  
            break
        resolution = stream.resolution
        if resolution not in seen_resolutions:  
            filesize_mb = stream.filesize / (1024 * 1024)  
            formatted_filesize = f"{filesize_mb:.2f} MB"
            video_info.append([resolution, formatted_filesize, stream.mime_type.split('/')[-1]])  # Add to video_info
            seen_resolutions.add(resolution)  

    # Fetch audio streams, sorted by bitrate in descending order
    audio_streams = yt.streams.filter(only_audio=True).order_by('abr').desc()

    # Create a list to store audio bitrates, file sizes, and file extension
    audio_info = []
    for stream in audio_streams[:2]:  
        filesize_mb = stream.filesize / (1024 * 1024)  
        formatted_filesize = f"{filesize_mb:.2f} MB"
        audio_info.append([stream.abr, formatted_filesize, stream.mime_type.split('/')[-1]])  # Add file extension

    # Fetch the best progressive stream (video + audio)
    progressive_streams = yt.streams.filter(progressive=True, file_extension='mp4').order_by('resolution').desc()
    video_audio_info = []

    # Only get the first (best quality) progressive stream
    if progressive_streams:
        stream = progressive_streams.first()  #
        filesize_mb = stream.filesize / (1024 * 1024)  
        formatted_filesize = f"{filesize_mb:.2f} MB"
        video_audio_info.append([stream.resolution, formatted_filesize, stream.mime_type.split('/')[-1]])  # Store resolution, file size, and extension

    dropdown_menu = c.CTkOptionMenu(main_frame,
    values=[
        "Downloading Options",  # This the Placeholder
        "@Video Only",
        f"  {video_info[0][0]}/{video_info[0][2]}  Filesize : {video_info[0][1]}",
        f"  {video_info[1][0]}/{video_info[1][2]}   Filesize : {video_info[1][1]}",
        "@Video + Audio",
        f"  {video_audio_info[0][0]}/{video_audio_info[0][2]}   Filesize : {video_audio_info[0][1]}",
        "@Audio",
        f"  {audio_info[0][0]}/{audio_info[0][2]}   Filesize : {audio_info[0][1]}",
        f"  {audio_info[1][0]}/{audio_info[1][2]}   Filesize : {audio_info[1][1]}"
    ],
    width=200,
    height=30,
    dynamic_resizing = False,
    font=("Arial",15),
    anchor=CENTER,
    fg_color="lightgrey",
    text_color="black",
    dropdown_fg_color="lightgrey",
    dropdown_text_color="black",
    dropdown_hover_color="white",
    button_color="lightblue",
    command=lambda x: handle_selection(x, dropdown_menu)  
)
    dropdown_menu.place(x=200,y=225)



def handle_selection(selection, dropdown):
    """
    Reset the value to deafult in case of wrong selection     
    """
    if selection.startswith("@") or selection == "Downloading Options":
        dropdown.set("Downloading Options")  
    process_selection(selection)


def process_selection(selection):
    """
    Filter the selection based on the user preference
    """
    url4 = my_entry.get()
    yt = YouTube(url4)

    if any(res in selection for res in ["1080p", "720p", "1440p", "2160p","480p"]):
        resolution = selection.split('/')[0].strip()  # Extract resolution
        stream = yt.streams.filter(res=resolution, progressive=False, file_extension='mp4')
    elif "kbps" in selection:
        bitrate = selection.split('/')[0].strip()  # Extract bitrate, e.g., "160kbps"
        if not bitrate.endswith("kbps"):
            bitrate += "kbps"  
        stream = yt.streams.filter(abr=bitrate, only_audio=True).first()
    else:  # Video + Audio (best quality progressive stream)
        stream = yt.streams.filter(progressive=True, file_extension='mp4').order_by('resolution').desc().first()
    # Using global function to access the variable 
    global select 
    select = stream
    global attr 
    attr = selection

def setting_widgets():
    """
    The check box and the download button setup on the GUI windows after the 
    feching the required Streams Available
    """
    global accept_check
    d_image = resource_path("Mandatory/download.png")
    download_image = PhotoImage(file=d_image)
    global download_button
    download_button = c.CTkButton(main_frame,text="Download ",
                                compound=RIGHT,image=download_image,
                                font=("Arial",20,"bold"),
                                command=download_video,          
                                height=35,
                                width=200)
    download_button.place(x=260,y=400)

    user = "Users must Comply with YouTube's Terms and Conditions when Downloading."
        
    accept_check = c.CTkCheckBox(main_frame,text=user,
                                    onvalue="yes", 
                                    offvalue="no",
                                    text_color="black",
                                    font=("Calibri",16,"bold"),
                                    )
    accept_check.place(x=40,y=360)

def progress_bar_update():
    """
    Update the Progress bar and text to 0 for futher downloads 
    and disapper progress bar along with the percentage downloading text 
    """
    progress_bar.set(0)
    percentage_label.configure(text="0%")
    percentage_label.destroy()


is_downloading = False
def download_video():
    """
    Performs exception checking, downloads the video to the desired location,
    updates the progress bar in real-time, and notifies the user upon successful download.
    """
    global progress, progress_queue, percentage_label, progress_bar , is_downloading
    # While downloading 
    if is_downloading:
        messagebox.showinfo("Download in Progress", "Please wait for the current download to complete.")
        logging.error("Download in Progress : Current Download to Complete")
        return  
    
    # Check user agreement and stream selection
    answer = accept_check.get()
    if attr is None or attr == "":
        messagebox.showerror(title="SelectionInputError", message="Please select the Stream to Download")
        return
    elif answer == "no":
        messagebox.showerror(title="AgreeTermsError", message="Please Accept the Condition ")
        return
    elif attr.startswith("@") or attr.startswith("D"):
        messagebox.showerror(title="AttributeError", message="Please Select the Valid Type from Options")
        return
    # Ask user for save path
    save_path = filedialog.asksaveasfilename(
        initialdir="/",  # Change this to your desired initial directory
        title="Save Video As",
        defaultextension=".mp4",  # Default extension
        filetypes=[("MP4 files", "*.mp4"), ("All files", "*.*")]
        )
    if not save_path:
            return
    is_downloading = True

    # Set up progress bar and label for showing download progress
    percentage_label = c.CTkLabel(main_frame, text="0%", anchor='e', text_color="black",
                                  width=350, font=("Arial", 15), bg_color="white")
    percentage_label.place(x=175, y=300)

    progress_bar = c.CTkProgressBar(percentage_label, width=300, mode="determinate")
    progress_bar.set(0)
    progress_bar.place(x=7, y=10)

    # Shared variable to hold progress
    progress = 0

    # Queue for communication between threads
    progress_queue = queue.Queue()

    def progress_callback(stream, chunk: bytes, bytes_remaining: int):
        """Callback function to update progress bar during download."""
        filesize = stream.filesize
        downloaded = filesize - bytes_remaining
        progress = downloaded / filesize  # Calculate download progress as a fraction
        progress_queue.put(progress)  # Put progress into the queue for main thread to process

    def update_progress():
        """Function to update progress from the queue in the main thread."""
        global progress
        try:
            progress = progress_queue.get_nowait()  # Try to get progress from the queue
            progress_bar.set(progress)  # Update progress bar
            percentage = int(progress * 100)  # Convert progress to percentage
            percentage_label.configure(text=f"{percentage}%")  # Update percentage label
        except queue.Empty:
            pass  # No new progress, keep waiting
        # Continue checking for progress updates every 100ms
        if is_downloading:
            win.after(100, update_progress)
        

    def download_task():
        """Background task to handle video download."""
        try:
            url5 = my_entry.get()  # Get video URL from entry widget
            yt = YouTube(url5)

            if any(res in attr for res in ["1080p", "720p", "1440p", "2160p"]):
                resolution = attr.split('/')[0].strip()  # Extract resolution
                stream = yt.streams.filter(res=resolution, progressive=False, file_extension='mp4').first()
                yt.register_on_progress_callback(progress_callback)
            elif "kbps" in attr:
                bitrate = attr.split('/')[0].strip()  # Extract bitrate, e.g., "160kbps"
                if not bitrate.endswith("kbps"):
                    bitrate += "kbps"  
                stream = yt.streams.filter(abr=bitrate, only_audio=True).first()
                yt.register_on_progress_callback(progress_callback)
            else:  # Video + Audio (best quality progressive stream)
                stream = yt.streams.filter(progressive=True, file_extension='mp4').order_by('resolution').desc().first()
                yt.register_on_progress_callback(progress_callback)

            # Start the download in the background (on a different thread)
            stream.download(output_path=save_path.rsplit('/', 1)[0], filename=save_path.split('/')[-1])
            progress_bar.set(1)  # Set progress bar to 100% when done
            percentage_label.configure(text="100%")  # Update label to show 100%
            time.sleep(1)
            messagebox.showinfo("Download Complete", f"{yt.title} has been downloaded successfully!")
            win.after(2000, progress_bar_update)
            logging.info("Video Download Successfully")
            
        except urllib.error.URLError:
            messagebox.showerror(title="NetworkError", message="Internet Not Connected")
            logging.critical("While Downloading : Internet Disconnects")
        except Exception as e:
            print(f"Error during download: {e}")
            logging.critical(f"Failure : {e}")
            messagebox.showerror("Download Error", f"An error occurred: {e}")
        finally:
            reset_download_state()

    def progress_update_task():
        """Task to update progress in a separate thread."""
        while progress < 1:  # Check while the progress is less than 100%
            update_progress()
            time.sleep(0.1)  # Update every 100ms

    # Start the download in a new thread to keep the UI responsive
    download_thread = threading.Thread(target=download_task)
    download_thread.daemon = True  # This ensures the thread exits when the main program exits
    download_thread.start()

    # Start the progress update in a separate thread
    progress_update_thread = threading.Thread(target=progress_update_task)
    progress_update_thread.daemon = True
    progress_update_thread.start()

def reset_download_state():
    """Reset download state when done."""
    global is_downloading
    is_downloading = False

def center_allocation(width,height):
    """
    Allocation the window screen to appear at the center on the window
    """
    sys_width = win.winfo_screenwidth()
    sys_height = win.winfo_screenheight()

    corner_x = int(sys_width/2 - width/2)
    corner_y = int(sys_height/2 - height/2)

    
    return corner_x,corner_y

def closing():
    """
    Prompt the user for confirmation to close the application 
    """
    response = messagebox.askyesno("Confirm Exit", "Do you want to close the application?")
    if response:
        logging.info("Application Closed")
        win.destroy()

# Capturing user activity using logging
logging.basicConfig(
    filename='activity.log',  
    filemode='a',                  
    level=logging.INFO,             
    format='root - %(asctime)s - %(levelname)s - %(message)s'  # Log format
)

c.set_appearance_mode("dark")

# custom Tkinter basic properties 
win = c.CTk()
win.config(bg="white")

width = 1050
height = 750
corner_x, corner_y = center_allocation(width, height)           
win.geometry(f"{width}x{height}+{corner_x}+{corner_y}")

win.title("YT Video Grabber")
win.resizable(False,False)
if sys.platform == "win32":
    icon_path = resource_path("Mandatory/YTicon.ico")
    win.iconbitmap(icon_path)
logo_image = resource_path("Mandatory/logo.png")
win.iconphoto(True,PhotoImage(file=logo_image))

win.protocol("WM_DELETE_WINDOW", closing)    # Title bar To prompt the user

warnings.filterwarnings("ignore", category=UserWarning, module="customtkinter")     # filter the warning raised by custom tkinter 

# Widgets and Their Properties set 
display_image_1 = resource_path("Mandatory/frame2.png")
image_1 = PhotoImage(file=display_image_1)
frame = Frame(win,height=750,width=300,bg="#F44236")
frame.pack(side="left", fill="y")


photo_image = Label(frame,image=image_1,bd=0, highlightthickness=0)
photo_image.pack(pady=(100, 0))

image_2 = resource_path("Mandatory/frame1.png")
display_image_2 = PhotoImage(file=image_2)
photo_image2 = Label(frame,image=display_image_2,bd=0, highlightthickness=0)
photo_image2.pack(pady=(50, 0))

image_4 = resource_path("Mandatory/entry.png")
entry_image = PhotoImage(file=image_4)
entry_icon = c.CTkLabel(win,height=35,text="",width=45,bg_color="white",image=entry_image)
entry_icon.place(x=310,y=198)

my_entry = c.CTkEntry(win,placeholder_text="Parse Youtube URL",
                      text_color="black",
                      placeholder_text_color="grey",
                      font=("Arial",15),
                      height=35,width=525,
                      fg_color=("black","white"),
                      justify="left",
                      selectborderwidth=25)
my_entry.place(x=365,y=200)

image_3 = resource_path("Mandatory/search.png")
search_image = PhotoImage(file=image_3)
search_button = Button(win,text="Search ",
                       font=("Arial",12,"bold"),
                       compound=RIGHT,
                       image=search_image,
                       bg="green",
                       height=35,
                       width=125,
                       command=check_url)
search_button.place(x=910,y=200,height=35,width=125)

logo_image = resource_path("Mandatory/logo.png")
logo = PhotoImage(file=logo_image)

label = c.CTkLabel(win,text=" YT Video Grabber",
                   text_color="red",
                   bg_color="white",
                   image=logo,
                   compound=LEFT,
                   font=("Tempus Sans ITC",60,"bold"))
label.place(x=450,y=50)

colour_code = "white"
main_frame = c.CTkFrame(win,fg_color=colour_code,
                        height=500,width=700,
                        border_color="black")
main_frame.place(x=365,y=265)

channel_label = c.CTkLabel(main_frame,text="",
                           height=40,width=450,
                           bg_color=colour_code,
                           anchor=W,
                           font=("Cascadia Code",18,"bold"),
                           text_color="black")
channel_label.place(x=240,y=5)

duration_label = c.CTkLabel(main_frame,text="",
                            height=35,width=450,
                            bg_color=colour_code,
                            anchor=W,
                            font=("Cascadia Code",16,"bold"),
                            text_color="black")
duration_label.place(x=240,y=50)

views_label = c.CTkLabel(main_frame,text="",
                         height=35,width=450,
                         bg_color=colour_code,
                         anchor=W,
                         font=("Cascadia Code",16,"bold"),
                         text_color="black")
views_label.place(x=240,y=90)

simple_title = c.CTkLabel(main_frame,text="",
                          height=45,width=700,
                          bg_color=colour_code,
                          anchor=W,
                          font=("Cascadia Code",18,"bold"),
                          text_color="black")
simple_title.place(x=5,y=150)


image_label = c.CTkLabel(main_frame,text=None,
                         height=140,width=230,
                         bg_color=colour_code)
image_label.place(x=5,y=5)

logging.basicConfig(
    filename='user_activity.log',  # Log file path
    filemode='a',                  # Append mode, so logs are added to the file
    level=logging.INFO,             # Minimum level to capture
    format='root - %(asctime)s - %(levelname)s - %(message)s'  # Log format
)
logging.info("Software initialized")
win.mainloop()