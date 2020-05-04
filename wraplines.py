defaultsize = 80

def wrapLinesSimple(lineslist, size=defaultsize):
    "Split at fixed position"
    wraplines = []
    for line in lineslist:
        while True:
            wraplines.append(line[:size])
            line = line[size:]
            if not line:
                break
    return wraplines

def wrapLinesSmart(lineslist, size=defaultsize, delimeters='.,:\t '):
    "wrap at first delimeter left of size"
    wraplines = []
    for line in lineslist:
        while True:
            if len(line) <= size:
                wraplines += [line]
                break
            else:
                for look in range(size-1, size//2, -1):
                    if line[look] in delimeters:
                        front, line = line[:look+1], line[look+1:]
                        break
                else:
                    front, line = line[:size], line[size:]
                wraplines += [front]
    return wraplines

def wrapText1(text, size=defaultsize):
    "when text read all at once"
    lines = text.split('\n')
    lines = wrapLinesSmart(lines, size)
    return '\n'.join(lines)

def wrapText2(text, size=defaultsize):
    text = text.replace('\n', ' ')
    lines = wrapLinesSmart([text], size)
    return lines

def wrapText3(text, size=defaultsize):
    lines = wrapText2(text, size)
    return '\n'.join(lines) + '\n'

def wrapLines1(lines, size=defaultsize):
    lines = [line[:-1] for line in lines]
    lines = wrapLinesSmart(lines,size)
    return [(line + '\n') for line in lines]

def wrapLines2(lines, size=defaultsize):
    text = ''.join(lines)
    lines = wrapText2(text)
    return [(line + '\n') for line in lines]

if __name__ == "__main__":
    lines = ['spam ham ' * 20 + 'spam, ni' * 20,
             'spam ham ' * 20,
             'spam, ni' * 20,
             '',
             'spam'*80,
             ' ',
             'spam ham eggs']

    sep = '-' * 30
    print('all', sep)
    for line in lines:
        print(repr(line))
        
    print('simple', sep)
    for line in wrapLinesSimple(lines):
        print(repr(line))

    print('smart', sep)
    for line in wrapLinesSmart(lines):
        print(line)
    
    print('single1', sep)
    for line in wrapLinesSimple([lines[0]], 60):
        print(repr(line))
    
    print('single2', sep)
    for line in wrapLinesSmart([line[0]], 60):
        print(line)

    print('combined text', sep)
    for line in wrapLines2(lines):
        print(line)
    
    print('combined lines', sep)
    print(wrapText1('\n'.join(lines)))

    assert ''.join(lines) == ''.join(wrapLinesSimple(lines, 60))
    assert ''.join(lines) == ''.join(wrapLinesSmart(lines, 60))
    print(len(''.join(lines)), end=' ')
    print(len(''.join(wrapLinesSimple(lines))), end=' ')
    print(len(''.join(wrapLinesSmart(lines))), end=' ')
    print(len(''.join(wrapLinesSmart(lines, 60))), end=' ')
    input('Press enter')