with open('/dev/input/js0') as js:
    with open('/dev/input/mouse0') as ms:
        while True:
            print('Joysticks', js.read(5))
            print('Mouse', ms.read(5))
