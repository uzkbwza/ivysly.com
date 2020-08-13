#!/bin/sh
python footnotes.py
echo "running footnotes script"
echo "generating blog"
cd pelican && make publish
cd ..
echo "removing existing blog contents" 
rm -r blog/*
echo "copying pelican output contents to blog folder"
cp -r pelican/output/* blog
