import gmic
gmic.run("""  camera w ${"fitscreen {[w,h]}"},0,"G'MIC Webcam Demo"
  for {*}" && "!{*,ESC}
    rm camera
    +b 0.5% lightrays. , n. 0,255 blend add,0.9
    w.
    wait 30
  done
  camera 0,0

""")
