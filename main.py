import random
from fastapi import FastAPI, Request, Form
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse

app = FastAPI()

mydata = open('fortunes.txt','r').read().split()

app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")

def get_counts(data):
    """Gets bigram and unigram counts for the fortunes corpus."""
    
    bigrams = {}
    unigrams = {}
    for i in range (len(data)-1):
        start = False #represents start of a new sentence 
        count = 1
        key = (data[i], data[i+1]) #declare key before using it  
        if(data[i] == '.' or data[i] == '!' or data[i] == '?'): #punctuations that end sentences
            key = (data[i], '#') #reassigning key value because we want punctuation to be followed by '#' as a key value 
            start = True 
        else:
            key = (data[i], data[i+1])
        if key in bigrams: #if the bigram already exists in the dictionary 
            bigrams[key] = bigrams[key] + 1 #increases count of bigram
            if(start == True): #if the start of a sentence is found, create a key in which '#' precedes the first word
                if(('#', data[i+1]) in bigrams):
                    bigrams[('#', data[i+1])] = bigrams[('#', data[i+1])] + 1
                else:
                    bigrams[('#', data[i+1])] = count 
        else: #if the bigram does not exist in the dictionary yet 
            bigrams[key] = count
            if(start == True): #as stated above, create a bigram for the start of a sentence when end of a sentence is found 
                if(('#', data[i+1]) in bigrams):
                    bigrams[('#', data[i+1])] = bigrams[('#', data[i+1])] + 1
                else:
                    bigrams[('#', data[i+1])] = count 

    for i in range (len(data)):
        count = 1
        key = (data[i])
        if key in unigrams:
            unigrams[key] = unigrams[key] + 1
        else:
            unigrams[key] = count
    unigrams['#'] = unigrams['.'] + unigrams['!'] + unigrams['?'] #total number of sentence endings
    
    return bigrams, unigrams

def bigram_model(data):
    """Builds the bigram model based on the uni/bigram counts."""

    bigrams,unigrams = get_counts(data)
    model = {}

    for k,v in bigrams.items():
        model[k] = (v / unigrams[k[0]]) #dividing each bigram count by the unigram count of its first member

    return model

def generate_sentence(model):
    """Uses bigram model to generate a new sentence."""

    begin = False
    end = False
    sentence = ''
    
    options = createMap(model) #find bigrams faster using options dictionary  

    while(begin == False): # selects a random starting point which is indicated by '#'
        start = random.choice(list(model.keys()))
        if start[0] == '#':
            begin = True #sentence start found 
    sentence = (sentence) + start[1]
    
    cont = random.choice(list(model.keys())) #get a random bigram 
    while(end == False):
        if cont[0].lower() == start[1].lower(): # check if the selected bigram is valid by comparing previous word in sentence to first word in selected bigram
            #if(model[cont] > 0.09): #tried using probabilities to create more accurate reults, run time increases 
            sentence = (sentence) + " " + cont[1] #add word onto sentence 
            start = cont # resets the start to find the next word
            if(cont[1] == '#'): # end of sentence found
                sentence = sentence.rsplit(' ', 1)[0] # get rid of "#" at end of the sentence
                end = True #end of setence found, exit loop 
            if((len(sentence)) > 50): # if it takes too long to find end of sentence, end it based on its length
                end = True
        if(start[1] in options): #created this if condition in case a word in not in options (text corpus could have errors)
            l = options[start[1]] #list of possible bigrams 
            rand = random.choice(l) #choose a random bigram from list 
            cont = rand #reset value for next possible bigram 
        else: #if word is not in options 
            cont = random.choice(list(model.keys()))
    return sentence

def createMap(model):
    """Helper function that builds map based on the model generated."""
    
    options = {}
    for k,v in model: #for each bigram 
        if(k in options): #if a list already exists for a word, k 
            options[k].append((k,v))
        else: #if k in not already a key in options 
            options[k] = [(k,v)] #create a new list whose first value is a tuple of the respective bigram 
    return options 

@app.get("/", response_class=HTMLResponse)
async def demo(request: Request):
    mymodel = bigram_model(mydata)
    fortune = generate_sentence(mymodel)
    return templates.TemplateResponse("index.html", {"request": request, "fortune": fortune})
