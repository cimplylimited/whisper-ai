from openai import OpenAI
import os
import json
import datetime

# The purpose of this script is to take a transcription and to build an article summary.
# This version makes a small change which asks AI to write in the 1st person.

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Set the OpenAI API key from the environment variable

# Define a function to get model completion
def get_completion(prompt, model="o1-preview"):
    messages = [{"role": "system", "content": prompt}]
    response = client.chat.completions.create(model=model,
    messages=messages,
    temperature=0.5)
    return response.choices[0].message.content

# Input variables
contents = [
f"""
Cimply | Marketing Strategy Bi-Weekly - 2024/11/19 12:00 EST - Transcript
Attendees
Daniel Kowal, Mark Donatelli, Mark Donatelli's Presentation
Transcript
Mark Donatelli: 
Daniel Kowal: 
Daniel Kowal: All right, good to go.
Mark Donatelli: I think we're good to go.
Mark Donatelli: So, Dan, yeah. So, I'm going to be working on a campaign to do some outreach on these local agencies. some do paid media, there's a little bit of a range there, but I'm working on the story of…
Mark Donatelli: how I want to approach them. And so, that you were talking about the setup. I'd like to be able to say, "Hey, Does this situation fit you? If so, let us know." that's the way I'm picturing it. But what were you about to say on that front?
Daniel Kowal: I think there are probably a few good signals that we can get that make us onboarding and…
Daniel Kowal: integrating from a managed service perspective as seamless as possible with a prospective agency. one of the criteria that comes up comes to mind is that they have between probably I want to say 50 and 200 employees or really 50 employees and up as just a loose framework. None of these things are perfectly defined but it's a good indicator if they've got 50 and up in terms of employees. it is a good indicator if they have an existing search, social or SEO practice that is sophisticated.
Daniel Kowal: It is a good sign if they have well-defined processes around how they functionally manage those paid media channels and it's a good sign if they are using the majority of their support inside the United States.  Those are good signals to be watching for.
Mark Donatelli: So, I think some of these agencies that I'm looking at, I know that one of them does a lot of health care and manufacturing type, B2B and healthcare type stuff. one of them we did the website for some big park system at the local park system or it wasn't the national park but the Chicago Valley Park or something metro parks or something. so there's definitely a wide range of industries they focus on.
Mark Donatelli: Is there something I know we talked in our profiling on our ICP stuff. I have those notes too. Let me see where those at. Yeah.
Daniel Kowal: the industry profile almost does not matter.
Daniel Kowal: They can be B2B or B TOC and they can be at any size or any vertical. the fact that they don't have existing media departments that are sophisticated and running at the moment makes them good candidates for consultative and potentially referral situations where they can come us, recommend us to their clients and…
Mark Donatelli: Yeah.
Daniel Kowal: have us manage that client relationship direct.  and maybe we have some referral agreement with those agencies if it's favorable. the other way that has manifested in the past has been through the way that we did the quantity relationship where they were a creative shop that did not have media services.  They went to our client who was precision and then we worked for precision powering their media from scratch. That is an okay arrangement.  It' that's a bad thing, but it creates a number of additional learning curve issues where the agency that we're contracting with doesn't fully understand the channel and the clients in theory might not fully understand the channel, especially if they're going to a creative agency to go get media services.
Mark Donatelli: Yeah. Heat.
Daniel Kowal: So, it's maybe second best or something, and it's definitely stuff we should continue to pursue. it should be on the list of ones to go after.  If we find one that has all the criteria that I had mentioned before, that one is let's keep getting on the phone with that person because they're going to come into a position where they're either onboarding a new client that is going to require significant resources to get all of the existing infrastructure moved over to the new agency.  or in some cases like what we're doing right now with Barkc we're filling in temporarily with a pitch to manage the media long term and they're making a transition from house to managed service through the agency relationship with Acadia not through us directly.
00:05:00
Mark Donatelli: Yep.
Daniel Kowal: those two relationship sets are distinctly you know what I'm saying that so if there's a situation where they've already got the same thing with Cardinal was a wellestablished but nearly as polished agency group their primary focus was on healthcare oriented companies for the most part it  was not pharmaceuticals across the board. It was mostly doctor's offices with 10 plus locations is probably the right way to say it. highly localized, not particularly specific in terms of what kind of healthcare they provided.
Daniel Kowal: 
Daniel Kowal: So it would be just out of recollection like dental offices, maybe some cosmetic surgery, psychiatry type services, physical therapy, a lot of kind of general care stuff. I could see optometrists being a good segment for us to maybe go after with those kinds of brands. and their processes, as some of the things that were not as good. they were stretched way too thin. They had really serious resource constraints. They didn't seem super interested in trying to figure out how to optimize the resource constraints in a way that was going to streamline and…
Mark Donatelli: Yeah.
Daniel Kowal: and remove some of the stress from the teams. The teams therefore didn't really have enough time to deeply consider the accounts that they were working on. let's say they had seven accounts each. They probably should have had six. And if they had six, they would all be working at a much more optimal vibration, but they were just kind of always stretched for time. so yeah, new onboardings and existing bridge services are both really good places for us to try to slot in. And then also sometimes there are situations where there are clients that are existing clients but again they're overwhelmed and…
Mark Donatelli: Yeah.
Daniel Kowal: overworked at the agency and they need somebody to come in and take a look at a troublesome issue and try to diagnose how we can turn the relationship around.  There'll be something valuable in there. I don't know what. So, yeah. I don't know what else you want to riff on about the paid search, social, SEO. I think it's really good for us to stay focused on those three services because they're very easy for us to slot in very quickly, prove our credibility.
Daniel Kowal: We're going to be faster than any other contractors in terms of being able to onboard to their accounts and get fully up to speed. New hires take 90 days to even start returning value. We can be fully up to and…
Mark Donatelli: 
Daniel Kowal: running in 10 business days, maybe less, in a lot of cases less than 10 business days that we're really kind of cruising and…
Mark Donatelli: Yeah, good.
Daniel Kowal: working the account. so yeah.
Mark Donatelli: So, FYI, the way this transcription works in Google, it will email the organizer the transcript.
Daniel Kowal: Yeah. Yeah.
Mark Donatelli: So, we'll just have to build a little process about what we do with that. We'll put them into the status folder, I'm assuming, because we'll see how it's named and I'll be curious to see how it's named and all that. It may just be obvious where it goes right into the status folder. Yeah.
Daniel Kowal: Yeah, if they have clean identifiers, even if they're not super well organized, We'll drop them all into a single folder and then we can start getting the programs that I have for transcription and summaries pointed to those repositories and we can start working on trying to automate this out…
Mark Donatelli: 
Daniel Kowal: because we can build something that'll do something even if it takes a while.
Mark Donatelli: Yeah, I mean basically I want to be able to produce from all this content,…
Mark Donatelli: right? One, I'm already experimenting with producing just these taglines to use with calls to action on social, that are meaningful and clever and build recognition or association of our brand with certain topics or certain ways of thinking. another stage from that, as the corpus gets larger or more refined, I want to be able to say, "Okay, I'm going to be sending out an email to these six people at these types of agencies that do this type of work in these categories for these types of, really beef up the prompt and say, hey, how do I write an email that's going to be extremely personalized and
Daniel Kowal: Yeah. Yep.
00:10:00
Mark Donatelli: 
Mark Donatelli: and relevant or…
Daniel Kowal: Mhm. Right.
Mark Donatelli: etc etc because again start I still need to get the message right to get reaching out because this is the way I think we're going to be able to like every person on that particular list specifically I've met face to face before right so that's a good thing for me that I'm like hey what these are all people that I know if I'm like hey let's have a cup of coffee I want to pick your brain about some stuff.
Daniel Kowal: 
Mark Donatelli: You're an agency person. Is for Is that a problem for you?
Daniel Kowal: Yeah, they're all competitors.
Mark Donatelli: Because I think that's kind of where because again I want to be able to probe them and figure out where are their gaps? this is part of as a product manager this is where that product market fit understanding comes from you got to keep asking your customers questions.
Mark Donatelli: 
Mark Donatelli: So, I want them to be customers, but sometimes they might also be competitors, too. But I don't think that's a problem.
Daniel Kowal: They're all competitors and we're going to have to be careful at some point of how big we get with the managed services and also what the clauses look like in terms of non-compete. but I think that in this particular case,…
Daniel Kowal: it looks like they're partners, suppliers, like that kind of stuff or something like that. Maybe not suppliers, they're partners and clients. we can even with them being competitors, I think there's enough room for everybody.
Mark Donatelli: In some of this,…
Mark Donatelli: there's two ways to position it in these cases, right?
Mark Donatelli: So, you're a one-legged man in an asskicking contest. do you need some help? Clearly, you can go win business. Let us help you keep it by keeping them happy. Let's help you deliver on the promise. Right? That's  Another thing is hey you need a scalable operation that's effective in order to grow. So now it's a consulting play as well you become a consultant inside of the agency helping them improve their own operation.
Mark Donatelli: 
Mark Donatelli: The question is how do you some people you'd want to approach for the first way and be like hey you're due for an overhaul. don't let some consultancy try to tell you how to run your agency. don't hire a consultant to come help you fix your business.
Daniel Kowal: And we're going to work on
Mark Donatelli: Hire an agency who's are consultants. That's us. Let us show you how to do this.
Mark Donatelli: 
Mark Donatelli: That to me is a whole talk track that we could get again we can get the language model to produce that talk track that usage scenario that use case is hey again I still think there's value in the housing thing I still think there's value in the segment of these house of brands thing I think there's value the actual point where we acutely touch, Whatever that beach head is,…
Mark Donatelli: wherever that is, it's all of those things, and again this is like the product manager there's all of these different personas,
Daniel Kowal: For this whole segment for the agency for the brand direct and…
Daniel Kowal: even like to some degree, maybe even more so with the agency ser managed services stuff, we  probably are looking at a land and expand opportunity if we can get in the door through a media channel. So if we find our way in for paid search, we can land and expand either horizontally out through paid social, programmatic display, any of the other media channels that we might be able to help with. we also might kind of semihorizontally be sort of doing channel planning or analytics so we can expand that agency thing kind of to the fullest and then there's sort of a vertical way that we can go up the chain bridging towards the consulting components of this where we're helping them to optimize what they're doing.
00:15:00
Daniel Kowal: I think that the benefit for us in terms of not really starting from that perspective in a lot of cases and that's more where we don't already have the trust of the client. So this doesn't really apply to places where you're like I know this guy's phone number.
Mark Donatelli: Yes. What time?
Daniel Kowal: It's more like I know this guy's name and that they are the right person to talk to at Smuckers or something or whatever it is. we need to develop the level of trust necessary to allow them to feel comfortable giving us access to proprietary things. And I don't think that takes super long, but getting the actionable workout right, and synthesizing that for them with reporting that's highly valuable and changes their thought process.
Daniel Kowal: even starting to dive into measurement frameworks. Those let us say to somebody, we really understand your business and…
Mark Donatelli: 
Daniel Kowal: we'd like to understand it better because we can help you understand your business better if you give us more context because that's what's happening.
Mark Donatelli: Yeah. …
Daniel Kowal: They're giving me access to things they've never given an agency access to before and it's been Exactly.
Mark Donatelli: Once you're in there, that's what you do is you build that trust base relationship and as long as you're doing the right things and it's working, they have no reason to not give you what you asked for. as long as you're producing the work. And so yeah, that's definitely a good way to think about it. the trick is I mean this is where I know that we've got room we've got runway with you but not that much. You know what I mean? Like having that Yeah.
Mark Donatelli: I mean, having the ability to hire someone who also has the ability to build that trust and know when to ask, what I mean? that's hard to replicate sometimes. And so we got be  Yeah. Yeah.
Daniel Kowal: I don't know
Daniel Kowal: if that's what we're hiring. I think if we get landed in the right place, we can find either somebody who has strong analytical background and is interested in biddable marketplaces. They don't need to be necessarily interested in marketing per se. So, that's a skill set that we can certainly go and find at colleges. I had a guy reach out to me the other day cold about an internship and he actually looked somewhat qualified and I thought about it but he was an H1 visa type or something like that one of those student visas and I was like we don't have the capabilities to manage that…
Mark Donatelli: 
Daniel Kowal: but we could so an analytics biddable modeling kind of skill set works perfectly and then the second thing is that it's not that hard for us given the network we have to go  on.
Mark Donatelli: You're going what?
Mark Donatelli: You there? we lost Transcription still going, but Dan is not showing
Mark Donatelli: 
Mark Donatelli: Just a pause in the action on the transcription. Dan will come back soon.
Daniel Kowal: 
Daniel Kowal: Try this again from another browser.
Mark Donatelli: Yeah, the transcript didn't stop when you That's good. When you froze. So, I was talking to the screen.
Daniel Kowal: That's great.
Mark Donatelli: So, we'll see what's in the transcript. It just rattles on. It'll probably say you left and then came back, I assume. Maybe not.
Daniel Kowal: Yeah. I don't know.
Daniel Kowal: What was the last thing you heard?
Mark Donatelli: We were talking about we had kind of paused for a second,…
Mark Donatelli: but we were talking about f*** I was god damn it, we were talking about hiring people and I said that there was this potential scale question, and you'd said, that's probably not what we're hiring for." And I said, "Yeah, that's probably right." And then you were continuing to go on about …
00:20:00
Daniel Kowal: 
Mark Donatelli: I just think there's a quality layer there if that's part of our niche, then that should be part of our niche. …
Daniel Kowal: We need to get the absolute best.
Mark Donatelli: things we talking about
Daniel Kowal: We need to get the absolute best we can find. But I think that we will be able to cycle through a bunch of options and potential pipeline for who those people look like. That's going to be perfectly if we can get somebody to do the work and they can take the direction and they're interested in the way that we're thinking about things different because it's going to appear very apparently to somebody who's been doing this for a while that we're doing this differently than other people to a degree.
Daniel Kowal: 
Daniel Kowal: And if we can get that stuff sorted and then I can turn attention back towards maybe how we start thinking about some of this tooling and getting the applications starting to be developed so that hey give us this and…
Daniel Kowal: we can give you this output. Okay.
Mark Donatelli: Yeah, I think we have to think about that,…
Mark Donatelli: We got to think about how does that there's some ideation that I'd like to do with you on that before we go too far, I mean, we want to make sure that we're building the right thing.
Daniel Kowal: The only things that I'm building right now are if I see something that's not available in a particular account that I'm working on and it's a tool that I've used in the past or it's a tool that was part of the standard repertoire of something else that I was working on or it was a tool that had to be developed every time I got into an old account. or it's building on some advanced logic that the agency isn't using to make decisions like ROI oriented stuff.  If it's a management tool directly related to the job, I'm trying to build small little micro applications that are letting me do that at scale so that I can do the same thing for 10 people at the same time that I can't currently do for one.
Mark Donatelli: Right.
Daniel Kowal: 
Daniel Kowal: So it's mostly just coinciding with workflows at the moment and some of them are going to be more useful than others. But if we just keep iterating them out, the chat GPT stuff is making it much easier to deploy those things. I wanted to do that ROI analysis for Aadia. That's part of what won them the pitch was that ROI analysis. That was a cluster thing application that I built in a day and we can use that again and…
Mark Donatelli: 
Daniel Kowal: maybe not exactly word for exactly the way it is but generally we can start thinking about…
Mark Donatelli: Yeah. Sounds good.
Daniel Kowal: how that could be reused on any account that we were looking at that has the capability to return an ROI value and that ends up starting to be criteria for brand direct can you tell me what your customer acquisition cost is accurately can you tell me what your ROI is accurately how are you doing
Daniel Kowal: 
Daniel Kowal: that what first party tooling are you using? Those things all start to kind of make a lot more sense in the discovery process when we're going brand direct in some of this.
Mark Donatelli: What time is it? 1 o'clock.
Daniel Kowal: Yeah. We talked about Yeah.
Mark Donatelli: All agenda wise, let's see where we're at here. no.
Daniel Kowal: the transcription started. I mean, did you want to talk at all about any of the creative concepts that you're trying to go through or you want to just leave that until after you've started to get these taglines figured out?
Mark Donatelli: Yeah, I'm just letting you know where I'm at on that. I don't need any looked at yet. I mean, the things that I think it' be interesting is that ebook I put the link in the notes. one there's the term sheet I put in there, right? That you're going to take a look at that or talk to the legal about that. And then that ebook, one of the things that I'm trying to think about now because all I've done is I've basically organized a bunch of information. I need to validate a little bit of…
Daniel Kowal: Yeah. Yeah.
Mark Donatelli: what is said about these specific brands, I need to do some factchecking or insert some citations, right? I'd like to expand within each kind of chapter I need to insert some sort of an anecdote. whether it be previous life hive simply whatever any personal experience I have in a given topic I want to try and…
00:25:00
Daniel Kowal: 
Mark Donatelli: add some color right there might be some publicly citable stories in there the failing of Altria tobacco or…
Daniel Kowal: Yeah. Heat.
Mark Donatelli: whatever I don't maybe something interesting current eventish so anyway I'm missing some plugs I need to pull in more from the outside yeah exactly So,…
Daniel Kowal: I mean, I've had an incredible amount of success telling the GPT to review the work that's been done and having it give me a work sited list so that I know what it's pulling from and then go read the articles. You know what I mean?
Mark Donatelli: I'm getting close to feeding this back in and having it pay attention to certain spots and…
Daniel Kowal: 
Daniel Kowal: Yeah. Yeah.
Mark Donatelli: ask it for certain things to fill in. and then I'm going to con concept some artwork for it. just some diagrams or some photos from our library. I'm not crazy about the templates and I just wanted to see if I were to have this as a PDF somewhere what it might look like if I were to dress it up.
Daniel Kowal: This looks okay,…
Mark Donatelli: No,…
Daniel Kowal: it's not offensive.
Mark Donatelli: that's right. I was trying to get the blue. We talked about the blue before. …
Daniel Kowal: I can give you the color hash of that one that I used in the thing if we want a standard, if you like that particular blue as one option on our color palette, then I can give you what the hex is for that and then we know exactly what to put in.
Daniel Kowal: 
Daniel Kowal: and then Yeah,…
Mark Donatelli: so to that point. So, let me we're still on marketing, right? So,…
Daniel Kowal: I see the infinity right now.
Mark Donatelli: let me see if I can What am I going there? Is it infinity or you see my whole screen? f*** man.
Daniel Kowal: I see the social posts.
Mark Donatelli: So, let me go find something real quick here. I'm just trying to make the notinity not look the way it does. s***. What am I looking for? keynotes. there was thought I was just in here, dude. losing my mind,…
Daniel Kowal: This  Yeah.
Mark Donatelli: I'm losing my mind.  Let me stop sharing this for a second. I'm just trying to find a document that I just had open. I think I had it open. Is this is it. Maybe.  So, speaking of color palettes and all that, I think in this service mapping Keynote deck, there's a bunch of color stuff.
Daniel Kowal: Yeah.  Yeah.
Mark Donatelli: 
Mark Donatelli: I was messing around with gradients and so that blue that you have if you build a palette off of it there's a bunch of ways I was playing around with colors and I don't know I saw this palm t-shirt with these bars if we get a set of blues that we like, let's get the adjacent ones too and see how they look and then we can use them to accent stuff. I think again, I'm not saying we need 10 colors,…
Daniel Kowal: 
Mark Donatelli: but we need a couple within the grad with the adjacent gradients so we can use them to emphasize Yeah.
Daniel Kowal: Yeah, we probably do need 10 colors.
00:30:00
Daniel Kowal: Probably need 10 or 20 callers, but we …
Mark Donatelli: I was looking at old t-shirts.
Daniel Kowal: that's fine.
Mark Donatelli: These made me think of old t-shirts and stuff like I don't know.
Mark Donatelli: So I just want to throw that out there because that was something that came to mind. let me see if I can
Daniel Kowal: Yeah. Yeah,…
Daniel Kowal: they're good. we're going to have, one at a time.
Daniel Kowal: 
Daniel Kowal: I think one at a time we should try to go through the colors and start building some stuff in that we like. And I put that light blue in the status sheet.
Mark Donatelli: 
Daniel Kowal: So you can just take that one. You didn't seem to have a problem with it. I didn't have a problem with it. So sounds like it's approved as an option for something that we would use. And we can just keep building on that one at a time.
Mark Donatelli: And so I mean obviously within the and…
Mark Donatelli: I think within the template whether it's a keynote template or…
Daniel Kowal: And we can also I didn't say anything.
Mark Donatelli: go ahead I was going to say that how we use it I think is something that would go into that stylesheet like that we'd be like okay it's Can you hear me? Hello. …
Daniel Kowal: I can Yeah. Yeah. I'm cutting in and out, so I'm going to put myself on. Go ahead.
Daniel Kowal: 
Mark Donatelli: I was just saying that we should just be specific about how we use it. because again, it's a good accent. I like it. But yeah, we got to figure out how we're going to use it best.
Daniel Kowal: let me show you something about…
Daniel Kowal: how I'll do some of the color theory stuff sometimes. I don't know if you do this, but let me see if I can find the picture. I'm going to let me see if I can show you something really quick. One second. So
Mark Donatelli: Did you see that guy on Instagram? the guy, Mindful Pallets. He's got a really interesting approach to creating color palettes. He's got dozens of them which He gives you all the codes and everything. Dan left the meeting again.  He's got Internet blues. He's back. Callers. And he's gone again. He's gone.
Daniel Kowal: 
Mark Donatelli: And he's back.
Daniel Kowal: I can't hear anything you're saying if you're talking right now.
Mark Donatelli: The transcription here is all this is going to be funny in the trans.
Daniel Kowal: Let me see if my speaker is off. Yeah, I can't hear you at the moment.
Mark Donatelli: Is this captioning working?  Can you see the closed captioning I turned on for you, brother?  Lol. Bro, it's the tinfoil, I think.  All right. Meeting adjourned.
Meeting ended after 00:34:33 👋
This editable transcript was computer generated and might contain errors. People can also change the text after it was created.



"""
]

prompt = f"""Please review the content from a meeting transcript.  Your task will be to create an output file that our team can use to review and plan for the future.  It should be comprehensive:  
 - First, take extra time to review the whole transcript and organize the main ideas. 
 - Then review your analysis to extract key takeaways and next steps,
 - Then review the analysis against the transcript to see if anything important is missing,
 - Then create an outline of the content topics major headlines,
 - Then bullet out important points for the outline headings,
 - Then write a summary that is comprehensive and detailed
 - Then create a Title for the summary based on the title of the meeting itself in the transcript with attendees and a date/time of the meeting,
 - Then put together Next Steps and To Dos and assign them to an owner
 - Then ideate on key current and future strategic initiatives to focus on and organize them according to topics

 \n"""

for index, content in enumerate(contents, start=1):
    prompt += f"{index}. Content: {content}\n"

# Define the instruction for the model

instruction = f"""

Your goal is to make a comprehensive summary of a meeting, organize the meeting key points into an outline, showcase key next steps, and highlight any thought starters for strategic initiatives and priorities

When you are finished creating the summary, you must create a well-structured JSON response with a consistent format.   
Please do not let response variables show up more than once, make sure to use '\\n' for 
each new line, and make sure the json output is perfectly structured before returning it:

{prompt}"""  # Double curly braces to escape literal curly braces

# Get the response from the model
response = get_completion(instruction, model="gpt-4-1106-preview")

# Replace '\n' with actual newlines in the JSON content
response_with_newlines = response.replace('\\n', '\n')

# Manually format the response to ensure the desired structure
formatted_response = f'{{\n    "response": {response_with_newlines}\n}}'

# Prompt for the desired filename
output_filename = input("Enter the filename for the JSON output (e.g., quotes_output.json): ")

# Define the path to save the JSON file
file_path = os.path.join(os.getcwd(), output_filename)

# Save the response as a JSON file
with open(file_path, "w") as json_file:
    json_file.write(formatted_response)

print(f"Response has been saved to '{output_filename}' in the current directory.")
