from openai import OpenAI
import os
import json
import re

# Initialize the OpenAI client using your method
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# ==========================
# User-Defined Variables
# ==========================

# OpenAI model configuration
MODEL_NAME = "o1-preview"  # Adjust the model as needed

# System prompt and instruction prompt are combined in the main prompt
MAIN_PROMPT = """
You are a helpful assistant tasked with reviewing a meeting transcript and converting it into a structured JSON summary that our team can use to review and plan for the future.

Please follow these instructions:

1. **Review the meeting transcript carefully** to ensure every key point is accounted for. Do not skip any important details.

2. **Extract Meeting Details**:
   - Identify and extract the meeting title, attendees, and date/time from the transcript.
   - Include these details in the output.

3. **Organize the content** into a logical, step-by-step summary, using the specified JSON format.

4. **Create the following sections in the JSON output**:
   - **title**: The extracted meeting title.
   - **date**: The extracted meeting date and time.
   - **attendees**: A list of attendees.
   - **summary**: A comprehensive and detailed summary of the meeting's content.
   - **outline**: An array of objects, each with a "heading" and "points" that bullet out important points under each heading.
   - **key_takeaways**: A list of key decisions and conclusions.
   - **next_steps**: An array of objects, each with "task", "owner", "due_date", "urgency_score", and "priority_score".
   - **strategic_initiatives**: An object with topics as keys and arrays of initiatives as values.

5. **Ensure compliance** by making sure all steps adhere to company policies, privacy regulations, and legal requirements.

6. **Important Notes**:
   - **Output only the JSON structure in your final response**. Do not include any explanations or additional text.
   - **Ensure that the JSON is properly formatted and valid**.
   - **All strings should be enclosed in double quotes**.
   - **Use `\\n` to represent newlines within string values if necessary**.
   - **Do not include any control characters that are invalid in JSON**.

Please produce the output in the following JSON format:

{
  "title": "Extracted Meeting Title",
  "date": "Extracted Meeting Date and Time",
  "attendees": ["Attendee1", "Attendee2", "Attendee3"],
  "summary": "Comprehensive and detailed summary.",
  "outline": [
    {
      "heading": "Main Topic 1",
      "points": ["Point 1 detail", "Point 2 detail"]
    },
    {
      "heading": "Main Topic 2",
      "points": ["Point 1 detail", "Point 2 detail"]
    }
  ],
  "key_takeaways": ["Takeaway 1", "Takeaway 2"],
  "next_steps": [
    {
      "task": "Description of the task",
      "owner": "Responsible person's name",
      "due_date": "Target date",
      "urgency_score": "Index of time to complete",
      "priority_score": "Index of how important this is related to potential impact"
    }
  ],
  "strategic_initiatives": {
    "Topic A": ["Initiative 1", "Initiative 2"],
    "Topic B": ["Initiative 3", "Initiative 4"]
  }
}
"""

# Transcript content
TRANSCRIPT_CONTENT = '''

00:00
Duke McKenzie
Oh wanted to include her on the call because she's, she's, she's helping ideate and come through processes of how we can make some impact. And then Tinashi, who is here, who just joined Tinashi, this is Mahesh also works on, on that side as well with the attribution and all of those things. And he runs Asani. So what we wanted to do is that maybe all of us may not be there on. I will be there, Ray will be there. And we're deciding who's coming for our, our conversation on the 8th, I believe it is 7th or 8th or whatever. 

00:36
Mahesh Ramachandra
Yeah, yeah, Michael is setting that up. 

00:39
Duke McKenzie
Yeah, yeah, Michael's setting it up. But the more, what's more important what we just wanted to do is we had like a couple questions came up while were working on these things and I'll start it off and we'll go from there and ask some questions. So the first question is that kind of came up over and over again was who is your buyer? We, we have some assumptions as to like, but like, and then the thing is like, who is the person that is actually like, there's two things you are targeting a demo to play, but then who is the one that you are targeting is the person that actually goes into the store and makes the purchase at retail to purchase the product. 

01:15
Mahesh Ramachandra
Okay. So the. And, and I don't think this, this target is going to change, by the way, you know, because we're, we're still new, we're still growing. But the, the buyers are young parents, right? So they've got parents of young families. Predominantly. They, we have a high propensity of like female mom buyers. Right? We have a lot of moms who are buying this device because, you know, they think it's, it's going to be. Oh, it is, you know, better screen time, right? So, so there's, yeah, so I think, I think, you know, and the, and the kids they have, you know, generally from four and up, right. And let's say the Sweet spot is 6 and 7. So these are families with young kids now. 

02:15
Mahesh Ramachandra
There might be, you know, an older sibling, there might be little babies and you know, somewhere in between, they're all playing together on this device. The, the buyers may or may not have other video game consoles. And, and we see, you know, next as being like, you know, completely compatible with that because we're not, we're not, you know, we're not really in direct sort of like competition with let's say a PlayStation or an Xbox or something like that. In fact, many of our customers do have both, but there are a lot of our. I'm saying the words a lot and all because I don't have exact numbers, but you know, that. Who also do not own any consoles at all. And they've been frightened of owning consoles and they haven't been comfortable buying consoles for their kids. 

03:08
Mahesh Ramachandra
And they've probably been dreading it when that time comes when the kids, you know, all want a PlayStation or they all want a Switch or something. Whereas the next is a very easy purchase for them because of the easy setup, no controllers and the relatively low price point. So that's kind of the target demo at the moment. There are a couple of smaller audiences as well. Gifting is important because it's very giftable. So we have a lot of grandparents buying the device and it's easy to pick up and play and you know, take over to grandma, Grandpa's house and you know, play there. And, and we see that as being a growing sort of like audience. But yeah, that's, that's our, the actual buyer. 

04:01
Duke McKenzie
Okay, so the core, the players are the most of the consumers are 4 to 7. The argument is that it's better screen time. Like, yes. And it's fun and physical activity and all those, the purchasers, the actual ones slapping their credit cards down are young, young parents, but young moms are the drivers of the purchase. Okay, and then for that you have. So I, you know, the team's aware that we did the execution with Giannis, who is in the, is in your demographic, has a young family and adorable young kids and all of those things there for your. This last tranche of activity that you did. What other things have you done? Like, have you done other live events? Have you created? Like, have you been doing any media buying like sc, SEO, Search or, or anything like that? 

04:52
Duke McKenzie
What, what have you done so far? 

04:54
Mahesh Ramachandra
Okay, so besides the, besides what we do on social media ourselves, both organic, some paid and you know, wherever we can collab with our IP owners, we've done that as well. So like, you know, Kung Fu, I mean, NBC DreamWorks have been great. They've done a lot of things with us. Patel have been terrible. They hard to get them to do anything. But you know, so, so, you know, we are trying to work on that. So that's the main thing we did do, we did do a brand, more like a brand campaign around, you know, Next Playground, which was more of a traditional media campaign, which we did, which is quite heavily, you know, featured on Smart TVs and streaming services. That's where we targeted that campaign. But apart from that, not really anything else. 

06:01
Mahesh Ramachandra
I mean, you know, there was an event that we did in New York in October I think, which was an event for, for the press and for influences, for micro influences. We had a lot of, you know, parent, you know, parent talk and you know, parent Instagram people and you know, parent influences there. So we did an event for them that was a live activation event, which, you know, I think, you know, was successful for them. And certainly we'd want to probably do more of those because the best thing with Playground is just being able to play, you know. Yeah. So and you know, and, yeah, and then apart from that, you know, we have a lot of performance marketing specifically for purchasing right now. We've slowed a lot of that way down because we are sold out. 

06:58
Duke McKenzie
Don't you have no units? 

06:59
Mahesh Ramachandra
We have no units. 

07:01
Duke McKenzie
You have no units. 

07:03
Mahesh Ramachandra
We have very few units. So that's a, a problem at the moment more than anything else. 

07:08
Duke McKenzie
It's a good problem, but still a problem. It's funny how life works, right? Okay. And then as I'm gonna keep on going, do you guys. Susan, Tashi, do you have any questions before I, I hop into my next one or. Because I'm dominating all the time. 

07:23
Susan Kilkenny
Well, you've been asking all of my questions. You know, and we had this, we re grouped last week, but I do have one related before you move on. So your units are basically sold out right now. But for 2025, are your, what are your goals? Is it like sell product? Is it subscriptions? Is it both? Like what's coming down the pipe? 

07:43
Mahesh Ramachandra
Yeah, so the, the business model for Playground is that the device itself sells for 199, $200 and that comes with five games. And the rest of the games are unlocked with annual subscription and the annual subscription is the 89 subscription. And as of right now, it's the, the conversion to buy that subscription or activate is really high. It's about 80 at the moment. So almost everybody buys it gets. 

08:17
Susan Kilkenny
Wow, that's great. 

08:18
Mahesh Ramachandra
Yeah. So that, so that's good. 

08:21
Duke McKenzie
And, and I don't mean to interrupt you, but you're, but the new Title that comes like the how you slay a dragon and a bunch of new ip that's going to be a part of the. 

08:29
Mahesh Ramachandra
Yes, the subscription. 

08:30
Duke McKenzie
Right. In order for me to get this new exciting activity and then your strategy, you're gonna always have news to. Yeah, I didn't mean to. 

08:38
Mahesh Ramachandra
Yeah, I mean, you know, it is, we have been talking about it and it is tempting to have like premium content that is not within the subscription. But I think at the moment the idea is to keep this, keep a simple subscription. And it's like you pay 89, you're gonna get all of the games and that's how we're doing it at the moment. And adding increasing amounts of value to your game package and then adding content updates and, you know, and content drops throughout the year. So that, you know, we want to keep you retained within that subscription. That's really the goal. We don't want to overcomplicate it for our customers, for parents and you know, and certainly there's no microtransactions, no advertising, nothing. 

09:21
Susan Kilkenny
Got it. And you don't have to really work that hard to sell the subscriptions. It sounds like, it sounds like the device buyer is automatically gone. Okay, cool. 

09:32
Mahesh Ramachandra
And then partly because we're also, in some cases, especially at retail, we're bundling it. So you get the next playground plus the, the, the carry. The carry case as well. So the carry case is 20, $25. So. So you get all three together as a bundle. 

09:52
Duke McKenzie
Okay, okay. And then, and then, so then, and then. Jump in, guys. If I, if I'm dominating, Dom. Dominating all the time. If. My question to you now is that I know we've talked briefly about licensing and potentially or like other things. Like we're going to include those on that. We're going to include that on the menu of some ideas we have around because we have some pretty. But to date with your, with your CPA type of stuff and whatever, how have you been attributing? Attribution has just been like codes or like, do you know what I mean? Like when you're saying, okay, this program worked, like right now everything is working because you're sold out. Right? But, but as you're growing and you're getting ready for your serious D and things like that, what have you been doing to measure attribution? 

10:38
Duke McKenzie
To say, okay, yes, this got me attention. This is driving sales or this like just top line. 

10:43
Mahesh Ramachandra
I mean, I think probably Safe to say we're at the early stages of that. Right. You know there are some programs that we have started and mixed very quickly. Like, like referral programs or you know, referral programs. We started and you know, we stopped those and I think because of complexity of managing them, sometimes we, I can't remember what it is. I mean we are doing, of course we're doing as much attribution as we can for our Facebook campaigns and our Insta campaigns and all of that. And you know, they all where possible lead back to a paid solution. And we, depending on, you know there are points where we, the default is always to send people to the, to Amazon because I think it's got the most reliable shipping. 

11:38
Mahesh Ramachandra
We have our own E commerce store which is like the ultimate kind of fallback. But in some cases we also direct traffic to your retail part. Your partners, Target Ecom and the Walmart E Comm as well. 

11:52
Duke McKenzie
And right now it's just in Target and Walmart, right? 

11:57
Mahesh Ramachandra
It's in Target, Walmart and Best Buy. 

11:59
Susan Kilkenny
And it's sold out everywhere. 

12:02
Mahesh Ramachandra
It sold out, yeah. Washington D.C. It is, it is. And next year, and I think we're in kind of like I can't remember the number of stores but like we're in about 2, 000 stores or just under. And next year we should be full chain so across all stores. And then the other partner that I think is coming in I think is Costco. So. But, but Costco is going to have a kind of, a separate, kind of. 

12:35
Duke McKenzie
You know, they always have something separate. What you're gonna have a Kirkland Lake brand. A Kirkland Lake bred. 

12:43
Susan Kilkenny
So can I ask you a question? It sounds like you have, it sounds like you're doing a lot of customer research because you understand your secondary targets and your, the propensities and you know there's always room to grow that way. So it sounds like from a performance and sales perspective as you have more products, you have strategies that you know that'll grow to sell product. But what about brand awareness? Like I, I had never even heard of this and I like have spent a lot of time in gaming. So I'm wondering like, do people know the brand and is that a focus for you? Okay. 

13:22
Mahesh Ramachandra
Yeah, yeah. The one, the one sort of area we, you know, I think we really suffer from is that we have no brand awareness. Right? We have no brand awareness whatsoever. And I Think obviously, that was one of the reasons we. We, you know, kind of, you know, did the. The activation with Cabbie, because I think I. I can't remember what we used to track our brand awareness, but that went through the roof, you know, so for. And when that campaign went out, so I think, you know, the association with Cabbie, with the anist, that's really helped. And that's also been our most untargeted campaign. Right. We know it's mess. It's a mass campaign and it's, you know. 

14:06
Susan Kilkenny
Right, yeah, but that's what brand awareness is. Right? Like, it should have different pillars under it, but like that the goal really is, you know, you have to figure out how to measure it. But. So do you plan on doing more of that, or are you trying to find a balance between sales and awareness or. 

14:28
Mahesh Ramachandra
I think. I think we do want to do more of that, you know, and. And probably, you know, probably we. We don't really know how to. I think it's probably the. In a way, I think. I think one thing, and maybe I'm speaking on behalf of our marketing people who know more about this than I do, but I think one thing for sure is that traditional media and advertising hasn't really worked for us, and it's very expensive. So I think, you know, the awareness campaign that we've built with our more traditional, you know, media campaign, we did, you know, that does nothing. Right. You know, I think, you know, what. What we did with the, With. With. With Cabbie, you know, as of right now, costs a lot less and had a lot, much larger impact. Right? So. So, So I think. 

15:16
Mahesh Ramachandra
I think that's promising to us. So at the back of our minds, which is the reason for having this, this get together early next year, is like, we're thinking, okay, how do we. How do we use, you know, social media and. And, you know, influencers, you know, to help open us up to certain audiences? How do we. How do we build our brand within, at least within certain audiences, plus driving, direct sales as well. But. 

15:45
Susan Kilkenny
Right. 

15:46
Mahesh Ramachandra
Yeah, but. But I think we. We want to. We want to figure out both. We want to have a balance of it, but we want to figure out how to do it right. How to do it right. 

15:54
Susan Kilkenny
Of course. 

15:54
Mahesh Ramachandra
Particular audiences. Yeah. 

15:56
Duke McKenzie
And in theory. Sorry, go ahead, Susan, go ahead. 

15:59
Susan Kilkenny
Well, I was just gonna ask. So, like, it doesn't have to be scientific, but from your perspective, or like, at least your conversations internally, from a brand awareness perspective, who do you imagine you should be engaging in order to really drive that brand awareness. Like, do you, have you put some thought into that? Like, it seems a little sports oriented, but it could be like Nickelodeon, like, I don't know. 

16:30
Mahesh Ramachandra
Yeah, yeah, I think so. So, so probably there's both certain types of audiences we want to reach as well as, you know, certain brands that we know we are working with already. So what we're doing right now with the brands that we've licensed, you know, it's at this point of time, it's to give us a little bit of credibility. Right? So on the box, you know, you get Kung Fu Panda, you get Barbie, you know, you get Sesame street purely for credibility. But next year, you know, I, and beyond, it's really about how can we leverage their audiences, you know, because they have really big reach and, and a lot of trust with, with families and love with families, you know, and we need to figure out ways to really make use of that so that, so that's one thing. 

17:26
Mahesh Ramachandra
And then, and then I think there are specific audiences that we're kind of, you know, conquer and win. Right. You know, and some of them are very, you know, very, very vague. But there's the mom audience, whatever that might mean. 

17:46
Susan Kilkenny
You know, but it's, but that's what I'm asking. Like, I don't expect, you know. 

17:50
Mahesh Ramachandra
Yeah, and, and there's things like, you know, there's pockets where, you know, we have a lot of, for example, families who do homeschooling love this device. Right. You know, so it's like, okay, how many is that then? Okay, that's a million households. Right? Okay, we get, how do we get 25 of those households or 37? You know, we, the, you know, there are, it's basically right now we've, we've sold like 150,000 devices. So the next target is over a million or more of these devices in home. And, and you know, we think we can do that, you know, and beyond that, it's, it's going up into the tens of millions. And we believe that there is a market there for us to get. But it is going to be a bit more specific about how do we capture each of these specific types of. 

18:44
Susan Kilkenny
Right. 

18:45
Mahesh Ramachandra
How do we capture the grandparents audience, for example? Right. You know, the, you know, there's, that, that, that's a, it's a problem as well. So I, I listen and you know, then yeah, then there's certain, there certain you know, genre categories which are interesting as well, like sports, you know, more educational, preschool etc. 

19:09
Duke McKenzie
And do you have any high. Okay, so Giannis is a high profile partner that is like obviously you might have to engage him in other. But like you have to ask to engage. But he seems to be willing to engage. 

19:19
Mahesh Ramachandra
Right? 

19:19
Duke McKenzie
Like he was willing to engage there. Is he your highest profile partner so far outside of Cabbie or there are other high profile partners that are potential. 

19:30
Mahesh Ramachandra
I, I think it's him. Yeah. I would say. 

19:33
Duke McKenzie
No, that's great. No, that's, I'm not that it's an embarrassment of riches. Okay. And, and he, in theory if we put something compelling down because I do know his like it's, I, it's probably from another life. I know his manager in theory he is supportive to engage and he seemed to have a lot of fun that day. 

19:50
Mahesh Ramachandra
And yeah, he's supportive and his, you know, his organization or his business, you know, they, they are or they're planning to, you know, invest in next as well. Yeah. Yeah. And, and you know, the background for that is because, you know, in, in nexus early it's early sort of life, it was a basketball training app and the NBA. The NBA invested in NEXT back in 2018, which is where we started because we built a basketball training app. It's still the number one basketball training app on the app store. And the NBA. Yeah, the NBA. The NBA are one of our original investors and we have, because of the NBA, we've got a whole bunch of sports stars and soccer stars and NBA players and you know, they're all Steve Nash and all, everybody's, they're all investors. 

20:52
Susan Kilkenny
That's incredible. Okay, great. 

20:54
Mahesh Ramachandra
And, and then you know, when the pandemic hit, we had to pivot to doing more games, you know, and then so more so now we still have a strong sort of like kind of sports slash fitness sort of angle, but it's broader than that. So, so we have good connections with the, you know, the sporting world and we're speaking to all of the leagues now. So mlb, NHL, NFL, all of them. And they all want some sort of experience on playground, which is great. 

21:23
Duke McKenzie
I love it. 

21:24
Susan Kilkenny
That's amazing. 

21:26
Duke McKenzie
Well, sports. The thing is, you have to get your kids to like. The thing is as, you know, so my. Now my kids are older, right? Not even older. I cannot believe I have an 18 year old and a 16 year old. So I don't even have kids anymore. But the thing is at that age of four to seven, you're. One of the things you're doing is how do you occupy them proper skiing time and all those. And sports like I do find we'll talk about internal, we'll circle up. But I do think. And the NBA, you're closest with the NBA. The NBA opens itself up. It's a, it's a very approachable league, younger demographic, young audience. 

21:58
Susan Kilkenny
What has its family programming and has its family programming. The fact that you have a relationship and an awareness with the actual players is incredible because it just becomes. It's trusted. Right. So like as your programming it, you know, grows and you go down the education route and the entertainment route for their children. I mean that's like a built in audience. You're in such a great place. 

22:25
Mahesh Ramachandra
Yeah, yeah, we hope so. We hope so. Yeah. And yeah, I think you know, being able to like, you know, get a taste or an experience of the sport, you know, in a fun way on the device. And, and again, it's about, also about accessibility. Right. Because you know, not, not everybody can play basketball or they may have different abilities or it may be winter or you know, there's different ways that the, that the device unlocks that a bit of that experience at home, you know, and, and that's kind of the, the angle we're taking with it. With, with that. Having said that, we do have like kind of a bunch of specifically basketball apps which are, I mean the experiences on various levels. Yeah. 

23:12
Duke McKenzie
All right now as we wind down, we have the last four minutes there tonight. You don't have. I didn't. I've been. 

23:17
Susan Kilkenny
Yeah. 

23:17
Tinashe Chaponda
Oh no, it's fine. 

23:18
Duke McKenzie
Y'all asked questions. 

23:20
Tinashe Chaponda
I was thinking, I just want to know. You talked about the different verticals you have social media influencers. You've done some performance. When you look at like the key driving vehicle, would you say that was your organic social infl. Like what's that one success main vehicle you think that really helped drive or is it because earlier you said because you're in an early stage difficult to really. 

23:43
Mahesh Ramachandra
I think it's probably hard to say and I think our team is kind of like kind of teasing that out. But you know, I think, I think the Definitely the more traditional advertising has not done much for us. And I think we've actually got a lot of engagement and virality through, through social media and UGC in general. And in fact, you know, if you go to our Facebook group, I think strongly suggest you go to take a look at our Facebook group, which is called Next Insider Community on Facebook. And we've got 13, 000 people on that group. Right. And they are highly engaged. No, sorry, 14, 500. I'm looking at it now. They're, they're highly engaged. 

24:40
Mahesh Ramachandra
You know, parents, for the most part, educators, you know, older siblings, etc, and everybody's giving tons of ideas about their experience with Next and they're posting videos and they're giving game suggestions and it's really active. Right. And, and we found that some of the best content and that plus some micro influences who are like parent influences have been pretty successful. And, and we can see the, the potential of doing more with that, you know, like big influencers, you know, some smaller micro influencers and then having, you know, certain audiences and who they particularly reach out to, I think is going to be. 

25:26
Susan Kilkenny
You said that the experience in New York was successful. And, and so giving people the opportunity to try the device is something that is a format that worked for you because I imagine you really have to get in there and to be w. Finding places to do that. 

25:44
Mahesh Ramachandra
Activations. Yeah, yeah, activations are great. Yeah. Wherever we've done it's been, it's been, you know, we've had a lot of, you know. Yeah, just getting anybody in front of it to just play. It's been a really positive experience. So we try to do that wherever possible. And. Yeah, yeah, that's generally been. Been good. I mean, our store experience, many of, not all of them, but many of the stores have a live demo experience in the store. So, you know, you can just walk up to the device, you know, raise up your hands and start playing. All right. And this has been great, you know, because you can just play in the store directly. 

26:27
Mahesh Ramachandra
And you know, we're, we're featuring different games in the stores and next year we're trying to have many more stores with these, these live demo experiences because it demos really well, you know, but that. 

26:39
Susan Kilkenny
So the store gives you a lot more real estate. 

26:49
Mahesh Ramachandra
Sorry, there's something ringing there. Yeah, sorry. 

26:52
Duke McKenzie
Yeah, I think she said the store gives you a lot More real estate was the question. 

26:56
Susan Kilkenny
And yeah, that's incredible. And that just makes your relationship stronger. Right? So that's awesome. 

27:02
Duke McKenzie
Yeah. Now I know we got mentioning on. 

27:04
Mahesh Ramachandra
The, worth mentioning on the stores, you know, like, we definitely want to do more with our retail partners next year super rush. But we would any sort of way we can think of engaging with them, you know, is something we would have done it with the, with the Cabby campaign. They Target wanted to do something. They were super happy to be involved with it, but he said just wasn't enough time. Yeah, four months, you know, they would have been involved in that. 

27:37
Duke McKenzie
I think that there's an opera. Definitely, definitely an opportunity for next time around while we, we're. We're, we're short. We got it. We, we now have to cut off the time because you're, we don't want to keep you. But quick question, the last question there is if you can ask your team what tail they, what tail? What, what tool they used or even if general how they've been measuring brand impact. If they had some type of tool or some type of whatever notion that would be useful for us to know what, how you've been doing that and. Yeah, no, we're excited. 

28:10
Tinashe Chaponda
Last, last thing real quick. Million, say a goal for a million units. Is that specifically for 25 or what was the Runway time you're hoping for? 

28:18
Mahesh Ramachandra
That's 2025, US only. 

28:20
Tinashe Chaponda
Okay, perfect, thanks. 

28:22
Mahesh Ramachandra
So at the moment we're only in the US we have ambitions to like do at least one more territory in 2025. It could probably be Canada. 

28:29
Tinashe Chaponda
Okay. 

28:30
Mahesh Ramachandra
You know, and we wanna, we want to do that. Yeah. And you know, I think the. And then, and then beyond that, 2025 and 2026 will be international, so. 

28:41
Duke McKenzie
Great. 

28:41
Tinashe Chaponda
Okay. 

28:42
Mahesh Ramachandra
We're trying to lay the groundwork for that a bit now. 

28:45
Duke McKenzie
Very good. Well listen, Mahesh, awesome. Thank you very much for your time. 

28:48
Mahesh Ramachandra
No, no, my pleasure. 

28:50
Duke McKenzie
I know you're not feeling well. Drink some more tea, my friend. And what time is it over there? What time is it over there? 

28:56
Mahesh Ramachandra
It's one more thing, Duke, if you can just speak with, with Ray as well. We still need that report, the campaign report for. 

29:06
Duke McKenzie
Oh, you don't have that yet. Okay. No, no. You mean other than the screen? Did you not get the screenshots we sent over? 

29:12
Mahesh Ramachandra
We got the screenshots, but weren't sure if there was more. More? Or is that. Is that it? Or. 

29:17
Tinashe Chaponda
Oh, like the actual report? 

29:18
Mahesh Ramachandra
Yeah, yeah. Because. Yeah, because it's hard to distribute it to everybody if it's just screenshots. 

29:24
Duke McKenzie
Okay, yeah. Tinashi, let's talk about it after. 

29:28
Mahesh Ramachandra
Or if it's all. If that is the oldest. 

29:30
Duke McKenzie
No, no, we can. We can put it in a more consumable format, like a nice PDF. 

29:34
Mahesh Ramachandra
A PDF? 

29:34
Duke McKenzie
Yeah, yeah, yeah, yeah. 

29:36
Tinashe Chaponda
Of course. 

29:37
Duke McKenzie
We'll make it consumable for you. 

29:39
Mahesh Ramachandra
We'll get it over to. 

29:40
Duke McKenzie
All right, thanks. Thanks again. 

29:42
Mahesh Ramachandra
Nice meeting you both. Nice meeting you as well. Merry Christmas. 



'''

# ==========================
# Main Functions
# ==========================

def is_system_role_supported(model_name):
    # List of models that support 'system' role in messages
    system_role_supported_models = ['gpt-3.5-turbo', 'gpt-4']
    return model_name in system_role_supported_models

def is_temperature_supported(model_name):
    # List of models that support the 'temperature' parameter
    temperature_supported_models = ['gpt-3.5-turbo', 'gpt-4']
    return model_name in temperature_supported_models

def generate_summary(transcript):
    # Combine the main prompt and transcript
    combined_prompt = f"{MAIN_PROMPT}\n\nTranscript:\n{transcript}"

    # Prepare the messages list
    messages = [{"role": "user", "content": combined_prompt}]

    # Prepare parameters for the API call
    api_params = {
        'model': MODEL_NAME,
        'messages': messages
    }

    # Add 'temperature' parameter if supported
    if is_temperature_supported(MODEL_NAME):
        api_params['temperature'] = 0  # or set to your desired value

    # Call the Chat Completion API
    response = client.chat.completions.create(**api_params)

    # Extract the assistant's reply
    assistant_reply = response.choices[0].message.content

    # Print the assistant's reply for debugging
    print("Assistant's reply:")
    print(assistant_reply)

    # Attempt to extract the JSON content
    json_match = re.search(r'\{.*\}', assistant_reply, re.DOTALL)
    if json_match:
        json_content = json_match.group(0)
        # Remove any content before or after the JSON object
        json_content = json_content.strip()
    else:
        print("Could not find JSON content in the assistant's reply.")
        return False

    # Validate and save the JSON output
    try:
        parsed_json = json.loads(json_content)
    except json.JSONDecodeError as e:
        print("JSON parsing error:", e)
        return False
    else:
        # Extract 'title' and 'date' to create a unique filename
        title = parsed_json.get('title', 'untitled')
        date = parsed_json.get('date', 'undated')

        # Sanitize filename components
        sanitized_title = sanitize_filename(title)
        sanitized_date = sanitize_filename(date)

        # Create the output filename
        output_filename = f"{sanitized_date}_{sanitized_title}.json"

        # Save the JSON to a file
        with open(output_filename, "w") as outfile:
            json.dump(parsed_json, outfile, indent=4)
        print(f"Response has been saved to '{output_filename}'.")
        return True

def sanitize_filename(value):
    # Remove any characters that are not alphanumeric, hyphens, underscores, or spaces
    value = re.sub(r'[^\w\s-]', '', value)
    # Replace spaces and hyphens with underscores
    value = re.sub(r'[\s-]+', '_', value)
    # Truncate to a maximum length if necessary
    return value.strip()[:100]  # Adjust length as needed

# ==========================
# Execution Block
# ==========================

if __name__ == "__main__":
    # Call the function to generate the summary
    success = generate_summary(
        transcript=TRANSCRIPT_CONTENT
    )

    if not success:
        print("Failed to generate a valid JSON summary.")