# See accompanying tutorial: https://discuss.pixls.us/t/developing-and-fiddling-with-the-gmic-python-binding/20406/3
import gmic
import random
import requests

output_filename = "myframe.png"
max_images = 70
filenames = []
for a in range(max_images):
    url = "https://picsum.photos/{}/{}".format(random.randint(50, 200), random.randint(50,200))
    filename = "picsum{}.png".format(a)
    filenames.append(filename)
    myfile = requests.get(url, allow_redirects=True)
    with open(filename, 'wb') as f:
        f.write(myfile.content)

gmic_command = "{} frame 3,3,0 frame 3,3,255 montage A display output {}".format(" ".join(filenames), output_filename)

gmic.run(gmic_command)
