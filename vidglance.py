from __future__ import print_function

import logging, os, re, shutil, subprocess, sys
from datetime import datetime
from decimal import Decimal
from PIL import Image, ImageFont, ImageDraw

video_extensions = [".avi", ".flv", ".m2ts", ".mod", ".mov", ".mp4", ".mpeg", ".mpg", ".mts", ".wmv"]

# input_dir = os.path.join("I:\\", "video backup")
# input_dir = os.path.join("I:\\", "video backup", "DAVGRA VIDJA STUFF", "d", "WEEJAH", "Handycam Compilation")
input_dir = os.path.join("I:\\", "video backup", "DAVGRA VIDJA STUFF", "d")
# input_dir = os.path.join("I:\\", "video backup", "DAVGRA VIDJA STUFF", "e", "My Videos", "Personal Projects")
# input_dir = os.path.join("I:\\", "video backup", "YouTube", "kylefavorites")
# input_dir = os.path.join("I:\\", "video backup", "YouTube", "test_thumbs")
output_dir = os.path.join("C:\\", "Users", "devgru", "video thumbnails")

script_dir = os.path.dirname(os.path.realpath(__file__))        # directory of the script

ffmpeg_path = os.path.join("C:\\", "ffmpeg", "bin", "ffmpeg.exe")


""" Represents a video file """
class Video:

  def __init__(self, path):
    self.path = path
    self.basename = os.path.basename(self.path)
    self.namewithoutext, self.ext = os.path.splitext(self.basename)

    self.output_w = 1920
    self.output_h = 1080

    self.num_rows = 5
    self.spacing = 2
    self.bbox_h = int((self.output_h - 40)/self.num_rows)
    self.thumb_h = self.bbox_h - 2*self.spacing

  def get_video_details(self):
    process = subprocess.Popen([ffmpeg_path, '-i', self.path], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    stdout, stderr = process.communicate()

    # logging.info(stdout)

    # Get video length
    matches = re.search(r"Duration:\s{1}(?P<hours>\d+?):(?P<minutes>\d+?):(?P<seconds>\d+\.\d+?),", stdout.decode("utf-8"), re.DOTALL)

    if matches is None:
      logging.error("Could not get duration for {}! Skipping thumbnail generation!!".format(self.path))
      return False

    matches = matches.groupdict()

    hours = Decimal(matches['hours'])
    minutes = Decimal(matches['minutes'])
    seconds = Decimal(matches['seconds'])
    total = 0
    total += 60 * 60 * hours
    total += 60 * minutes
    total += seconds
    self.length = total
    if hours > 0:
      self.length_string = matches['hours'] + ":" + matches['minutes'] + ":" + matches['seconds']
    else:
      self.length_string = matches['minutes'] + ":" + matches['seconds']
    
    # Get video resolution
    matches = re.search(r"Video:.+, (?P<xres>\d+)x(?P<yres>\d+)", stdout.decode("utf-8"), re.DOTALL).groupdict()
    self.resX = int(matches['xres'])
    self.resY = int(matches['yres'])
    self.thumb_w = int(self.thumb_h / self.resY * self.resX)
    self.bbox_w = self.thumb_w + 2*self.spacing
    self.num_cols = int(self.output_w / self.bbox_w)

    self.centering_offset = int((self.output_w - self.bbox_w*self.num_cols)/2)

    # Get creation date
    # matches = re.search(r"creation_time\s+: (?P<creation_time>\d+-\d+-\d+ \d+:\d+:\d+)", stdout.decode("utf-8"), re.DOTALL)
    # if matches is None:
    #   self.creation_time = ""
    # else:
    #   matches = matches.groupdict()
    #   self.creation_time = matches['creation_time']

    # self.creation_time = os.path.getmtime(self.path)
    self.creation_time = datetime.fromtimestamp(int(os.path.getmtime(self.path)))

    self.timestep = self.length / (self.num_rows * self.num_cols - 1)
    # if self.timestep < 5:
    #   self.timestep = 5
    self.fps = "{0:.8f}".format(1 / self.timestep)


    # logging.info(u"Getting video details for {}".format(self.path.encode('ascii', 'replace')))
    # logging.info("\t\t{0:>20s}: {1}".format("length in seconds", self.length))
    # logging.info("\t\t{0:>20s}: {1}x{2}".format("resolution", self.resX, self.resY))
    # logging.info("\t\t{0:>20s}: {1}".format("creation time", self.creation_time))
    # logging.info("\t\t{0:>20s}: {1}".format("num cols", self.num_cols))
    # logging.info("\t\t{0:>20s}: {1}".format("num_rows", self.num_rows))
    # logging.info("\t\t{0:>20s}: {1}".format("total", self.num_rows * self.num_cols))
    # logging.info("\t\t{0:>20s}: {1}".format("bbox width", self.bbox_w))
    # logging.info("\t\t{0:>20s}: {1}".format("bbox height", self.bbox_h))

    return True


  def generate_thumbnails(self):

    # Skip if already exists
    subdir = os.path.dirname(self.path).replace(":", "")
    if os.path.isfile(os.path.join(output_dir, subdir, self.namewithoutext + u"_thumbs.png")):
      return

    if not self.get_video_details():
      return

    logging.info(u"{0:>25s}: {1}".format("Converting Video", self.path))

    # logging.info(u"\t\t{}".format(self.path.encode('ascii', 'replace')))
    # logging.info("\t\t" + str(self.length) + "seconds")

    # Generate frames
    framesdir = os.path.join(output_dir, subdir, "frames_" + os.path.basename(self.namewithoutext))
    # logging.info(u"\t\tframe dir: {}".format(framesdir.encode('ascii', 'replace')))

    if not os.path.exists(framesdir):
      os.makedirs(framesdir)

    process = subprocess.call([ffmpeg_path, '-i', self.path, '-vf', 'fps=' + self.fps, os.path.join(framesdir, "%04d.png")])

    # Create new image and add header text
    final_image = Image.new("RGB", (self.output_w, self.output_h), "black")
    draw = ImageDraw.Draw(final_image)
    font = ImageFont.truetype("ARIALUNI.TTF", 16)

    string = u"File: {}".format(self.basename)
    draw.text((0, 0), string, (255, 255, 255), font=font)

    string = "Length: {}".format(self.length_string)
    draw.text((0, 20), string, (255, 255, 255), font=font)

    string = "Creation Date: {}".format(self.creation_time)
    string2 = "Time Step: {0:.2f}".format(self.timestep)
    x_offset, h = draw.textsize(string, font=font)
    w, h = draw.textsize(string2, font=font)
    if w > x_offset:
      x_offset = w

    draw.text((self.output_w - x_offset, 0), string, (255, 255, 255), font=font) 
    draw.text((self.output_w - x_offset, 20), string2, (255, 255, 255), font=font)    

    # logging.info("Size of string '" + string + "': " + str(w) + "x" + str(h))

    # Add frames and timestamps
    for idx, image in enumerate(sorted(os.listdir(framesdir))):

      r = int(idx / self.num_cols)
      c = idx % self.num_cols

      baseX = c * self.bbox_w + self.centering_offset
      baseY = r * self.bbox_h + 40

      # Draw current thumbnail
      img = Image.open(os.path.join(framesdir, image))
      img.thumbnail((self.thumb_w, self.thumb_h), Image.ANTIALIAS)
      # final_image.paste(img, (int(self.thumb_w * (idx % self.num_cols)), int(20 + idx//self.num_cols*self.thumb_h)))
      # final_image.paste(img, (self.bbox_w * (idx % self.num_cols) + 1, int(idx/self.num_cols)*self.bbox_h + 41))
      final_image.paste(img, (baseX + self.spacing, baseY + self.spacing))

      # Draw time string and it's background
      time_string = self.get_time_string(idx * self.timestep)
      w, h = draw.textsize(time_string, font=font)
      time_bkg = Image.new("RGBA", (w+2, h+2), (0, 0, 0, 128))
      final_image.paste(time_bkg, (baseX+self.spacing, baseY+self.spacing), time_bkg)
      draw.text((baseX+self.spacing, baseY+self.spacing), time_string, (255, 255, 255), font=font)

    # Cleanup temp directory
    shutil.rmtree(framesdir)

    # Save final image
    final_image.save(os.path.join(output_dir, subdir, self.namewithoutext + u"_thumbs.png"))

  def get_time_string(self, time):
    hours = int(time / 3600)
    minutes = int((time - hours*3600) / 60)
    seconds = int(time - hours*3600 - minutes*60)
    fraction = int((time - hours*3600 - minutes*60 - seconds)*100)
    if hours > 0:
      time_string = "{0:02d}:{1:02d}:{2:02d}.{3:02d}".format(hours, minutes, seconds, fraction)
    else:
      time_string = "{0:02d}:{1:02d}.{2:02d}".format(minutes, seconds, fraction)
    return time_string


"""
Check if output directory exists
"""
def check_output_dir():
  if not os.path.exists(output_dir):
    print("Output directory doesn't exist. Creating " + output_dir)
    os.makedirs(output_dir)


"""
Scan input directory for videos and return array of Video objects
"""
def build_video_dict_array():

  videos = []

  logging.info("Getting videos from input directory")
  for subdir, dirs, files in os.walk(input_dir):
    for filename in files:
      fn, ext = os.path.splitext(filename)
      # print(ext)
      for e in video_extensions:
        if ext == e:
          # logging.info(filename)
          videos.append(Video(os.path.join(subdir, filename)))
          
  return videos


""" ------------------------------------------------------------------------------------------------
Script Start
------------------------------------------------------------------------------------------------ """

timestart = datetime.now()

logging.basicConfig(filename='vidglance.log',level=logging.INFO)
# logging.basicConfig(filename='vidglance.log',level=logging.DEBUG)

check_output_dir()
videos = build_video_dict_array()

for v in videos:
  # v.log_info()
  v.generate_thumbnails()

print("Script took " + str(datetime.now() - timestart) + " to run.")

