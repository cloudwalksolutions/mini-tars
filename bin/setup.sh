#!/bin/bash


git config --global user.email "walkernobrien@gmail.com"
git config --global user.name "Walker O'Brien"

sudo cp -r config/pi ~

sudo usermod -a -G audio walker

sudo apt-get update -y
sudo apt-get upgrade -y

sudo apt-get install -y \
  python3-full \
  python3-dev \
  portaudio19-dev \
  python3-pigpio \
  pigpio \
  flac \
  libhdf5-dev

sudo pip3 install -r requirements.txt --break-system-packages

sudo pip3 uninstall gpiozero --break-system-packages -y

sudo apt-get remove python3-gpiozero -y
sudo apt-get install python3-gpiozero -y

sudo pigpiod

sudo apt update
sudo apt install snapd -y

sudo snap install core

sudo snap install starship --edge
sudo snap install --classic --channel=1.22/stable go

if [[ -z $OPENAI_API_KEY ]]; then
  echo "Please enter your OpenAI API key: "
  read OPENAI_API_KEY
fi

sed "s/{OPENAI_API_KEY}/${OPENAI_API_KEY}/g" config/rover.service.conf > config/rover.service

sudo mv config/rover.service /etc/systemd/system/
sudo systemctl enable rover.service

sudo cp config/stream.service.conf /etc/systemd/system/stream.service
sudo systemctl enable stream.service

sudo systemctl daemon-reload

sudo systemctl start rover.service
sudo systemctl start stream.service

