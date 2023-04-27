import mido
import json
import copy
import random
from fastapi import FastAPI

app = FastAPI()

def mid_to_json(mid, track_id=0):
    temp=[]
    new_data={'res':{}}
    new_data.get('res')['notes']=[]
    for i in mid.tracks[track_id]:
        if i.type=='note_on':
            new_data.get('res')['notes'].append({'on':i.note})
        if i.time:
            new_data.get('res')['notes'].append({'sysex':i.time}) 
        if i.type=='note_off':
            new_data.get('res')['notes'].append({'off':i.note})
    return(new_data)



major=[] #радостно, уверенно, весело
minor=[] #грустно, печально, сентиментально
dim=[] #неуверенно, испуганно, напряжённо
aug=[] #удивленно, сказочно, слегка пугающе
major7=[] #вдумчиво, мягко, легко, спокойно
chord7=[] #сильно, беспокойно, дерзко
minor7=[] #задумчиво, созерцательно, мягко, спокойно
minorsharp7=[] #беспокойно, угнетающе, пугающе
minor7b5=[] #неуверенно, раздражённо, слегка испуганно
dim7=[] #напряженно, испуганно, потерянно
major7sharp5=[] #удивленно, неожиданно, пугающе
sus2=[] #ощущение ожидания, легкого напряжения
sus4=[] #ожидание, легкое напряжение, предвкушение
for i in range(0,127-4-3-4):
    major.append([i, i+4, i+4+3])
    minor.append([i, i+3, i+3+4])
    dim.append([i, i+3, i+3+3])
    aug.append([i, i+4, i+4+4])
    major7.append([i, i+4, i+4+3, i+4+3+4])
    chord7.append([i, i+4, i+4+3, i+4+3+3])
    minor7.append([i, i+3, i+3+4, i+3+4+3])
    minorsharp7.append([i, i+3, i+3+4, i+3+4+4])
    minor7b5.append([i, i+3, i+3+3, i+3+3+4])
    dim7.append([i, i+3, i+3+3, i+3+3+3])
    major7sharp5.append([i, i+4, i+4+4, i+4+4+3])
    sus2.append([i, i+2, i+2+5])
    sus4.append([i, i+5, i+5+2])
    
def get_chord_by_emotion(emotion):
    switch_case = {
        "joy": major,
        "sad": minor,
        "scared": random.choice([dim,dim7]),
        "surprise": random.choice([aug,major7sharp5]),
        "calm": random.choice([major7,minor7]),
        "scary": minorsharp7,
        "angry": minor7b5,
        "suspense": random.choice([sus2,sus4,chord7])
    }
    if emotion in switch_case:
        return switch_case[emotion]
    else:
        return None 

circle_of_fifths=[0]
for i in range(0, 11):
    circle_of_fifths.append((circle_of_fifths[-1]+7)%12)

def get_min_length(notes):
    lens=[]
    for note in notes:
        if note.get('sysex'):
            lens.append(note.get('sysex'))
    return min(lens)

def get_melody_notes_per_chord(notes):
    return 4

def get_cycles(notes):
    min_length=get_min_length(notes)
    rhythm=get_melody_notes_per_chord(notes)
    cycle=[0]
    temp=0
    for i in range(len(notes)):
        if notes[i].get('sysex'):
            temp=temp+notes[i].get('sysex')
        if temp>=min_length*rhythm:
            cycle.append(i+1)
            temp=0
    if temp!=0:
        cycle.append(i+1)
    return cycle

def get_key(notes):
    for i in notes:
        if i.get('on'):
            break
    return i.get('on')


@app.post("/song")
async def get_song(data: dict):
    mid = mido.MidiFile()
    track = mido.MidiTrack()
    mid.tracks.append(track)
    
    for i in data.get('res').get('notes'):
        if i.get('on'):
            track.append(mido.Message('note_on', note=i.get('on')))
        if i.get('sysex'):
            track.append(mido.Message('sysex', time=i.get('sysex')))
        if i.get('off'):
            track.append(mido.Message('note_off', note=i.get('off')))

    #mid.save('new_song.mid')
    return mid_to_json(mid)

@app.post("/chords")
async def add_chords(data: dict):
    mid = mido.MidiFile()
    track = mido.MidiTrack()
    mid.tracks.append(track)

    chord = get_chord_by_emotion(data.get('res').get('emotion'))
    for i in data.get('res').get('notes'):
        if i.get('on'):
            for j in chord[i.get('on')]:
                track.append(mido.Message('note_on', note=j))
        if i.get('sysex'):
            track.append(mido.Message('sysex', time=i.get('sysex')))
        if i.get('off'):
            for j in chord[i.get('off')]:
                track.append(mido.Message('note_off', note=j))

    #mid.save('new_song_chords.mid')
    return mid_to_json(mid)

@app.post("/note2progression")
async def continue_note_to_progression(data: dict):
    chord3_p=[0,5,7,7,0,0,5,7,0,5,0,7,0,5,7,5]
    #blues_p=[0,0,0,0,5,5,0,0,7,5,0,0]
    
    mid = mido.MidiFile()
    track = mido.MidiTrack()
    mid.tracks.append(track)
    
    note=60
    time=120
    
    for i in data.get('res').get('notes'):
        if i.get('on'):
            note=i.get('on')
            break
    for i in data.get('res').get('notes'):
        if i.get('sysex'):
            time=i.get('sysex')
            break
        
    for i in chord3_p:
        track.append(mido.Message('note_on', note=note+i))
        track.append(mido.Message('sysex', time=time))
        track.append(mido.Message('note_off', note=note+i))
        
    #mid.save('new_song_progression.mid')
    return mid_to_json(mid)

@app.post("/note_circle")
async def continue_note_with_circle_of_fifths(data: dict):
    mid = mido.MidiFile()
    track = mido.MidiTrack()
    mid.tracks.append(track)
    
    note=60
    time=120
    
    for i in data.get('res').get('notes'):
        if i.get('on'):
            note=i.get('on')
            break
    for i in data.get('res').get('notes'):
        if i.get('sysex'):
            time=i.get('sysex')
            break
        
    for i in [major[circle_of_fifths[note%12-1]],major[circle_of_fifths[note%12]],major[circle_of_fifths[(note%12+1)%len(circle_of_fifths)]],
              minor[circle_of_fifths[note%12+1-9]],minor[circle_of_fifths[note%12-9]],minor[circle_of_fifths[note%12-1-9]]]:
        for j in i:
            track.append(mido.Message('note_on', note=note+j))
        track.append(mido.Message('sysex', time=time))
        for j in i:    
            track.append(mido.Message('note_off', note=note+j))
        
    #mid.save('new_circle_progression.mid')
    return mid_to_json(mid)

@app.post("/chords4melody")
async def add_chords_to_melody(data: dict):
    if (data.get("type") == "circle"):
        return add_chords_to_melody_with_circle_of_fifths(data)
    elif (data.get("type") == "emotion"):
        if get_chord_by_emotion(data.get("res").get("emotion")):
            return add_chords_to_melody_by_emotion(data)
        else:
            return "Emotion undefined"
    else:
        return "Type undefined"

def add_chords_to_melody_by_emotion(data: dict):
    mid = mido.MidiFile()
    track = mido.MidiTrack()
    mid.tracks.append(track)

    notes = data.get('res').get('notes')
    notes_cycle = get_melody_notes_per_chord(notes)
    notes_cycle_len = get_cycles(notes)
    chord = get_chord_by_emotion(data.get('res').get('emotion'))

    for i in range(len(notes_cycle_len)-1):
        cycle_notes=notes[notes_cycle_len[i]:notes_cycle_len[i+1]+1]
        melody_key = get_key(cycle_notes)
        for k in chord[melody_key]:
            track.append(mido.Message('note_on', note=k-24))
        for j in cycle_notes:
            if j.get('on'):
                track.append(mido.Message('note_on', note=j.get('on')))
            if j.get('sysex'):
                track.append(mido.Message('sysex', time=j.get('sysex')))
            if j.get('off'):
                track.append(mido.Message('note_off', note=j.get('off')))
        for k in chord[melody_key]:
            track.append(mido.Message('note_off', note=k-24))
        
    #mid.save('new_accompany_melody_progression.mid')
    return mid_to_json(mid)

def add_chords_to_melody_with_circle_of_fifths(data: dict):
    mid = mido.MidiFile()
    track = mido.MidiTrack()
    mid.tracks.append(track)
    
    notes = data.get('res').get('notes')
    notes_cycle = get_melody_notes_per_chord(notes)
    notes_cycle_len = get_cycles(notes)
    melody_key = get_key(notes)
    
    for i in range(len(notes_cycle_len)-1):
        cycle_notes = notes[notes_cycle_len[i]:notes_cycle_len[i+1]+1]
        random_chord = random.choice([major[circle_of_fifths[melody_key%12]],
                  major[circle_of_fifths[melody_key%12-1]],
                  major[circle_of_fifths[(melody_key%12+1)%len(circle_of_fifths)]],
                  minor[circle_of_fifths[melody_key%12+1-9]],
                  minor[circle_of_fifths[melody_key%12-9]],
                  minor[circle_of_fifths[melody_key%12-1-9]]])
        for k in random_chord:
            track.append(mido.Message('note_on', note=melody_key+k-24))
        for j in cycle_notes:
            if j.get('on'):
                track.append(mido.Message('note_on', note=j.get('on')))
            if j.get('sysex'):
                track.append(mido.Message('sysex', time=j.get('sysex')))
            if j.get('off'):
                track.append(mido.Message('note_off', note=j.get('off')))
        for k in random_chord:
            track.append(mido.Message('note_off', note=melody_key+k-24))
        
    #mid.save('new_accompany_melody_circle_progression.mid')
    return mid_to_json(mid)
    
