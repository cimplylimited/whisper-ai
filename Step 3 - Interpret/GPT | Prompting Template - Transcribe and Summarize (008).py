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
Cimply + VeraData Planning - 2024/11/25 11:28 EST - Transcript
Attendees
Mark Donatelli, Tom Hutchison
Transcript
Mark Donatelli: I think it started. Cool.
Mark Donatelli: 
Mark Donatelli: time we talked …
Tom Hutchison: Mhm.
Mark Donatelli: what came out of it at the end. I mean some of it's just getting me caught up on how Veridana operates and there's still some things there that we'll discover over time but in general the things that I brought in that profile notes document in the folder you should have access to that Sorry you didn't have access to it. I thought you did. before I brought some stuff up to the top kind of w wiki style where we'll just keep adding to it I guess. but from the last meeting you had talked about vera data is never experienced before optimization approach.
Mark Donatelli: 
Mark Donatelli: We also talked about four issues if you will. big picture stuff like what's the strategy?
Tom Hutchison: Yeah.
Mark Donatelli: Whether it's Chandis or Winterberry or whoever has been like, "Hey, you guys should be a platform." yet none of them know what the f*** that means. or how to do it. And then on the agency front not enough digital services not really integrated omni channel style. client they don't know. let me put a space in there. That's all kind of goes together right then.
Mark Donatelli: 
Mark Donatelli: And then this platform thing more immediately you talked about project Perry and kind of what that control panel might be. There could be some down market reporting or dashboard interactivity with Perry in some way. Matt is talking about data concier service like something like things that we might do that Vera data doesn't do. That's interesting. the stuff I shared with you, there's And again, this, right? We've been you and…
Tom Hutchison: Yes.
Mark Donatelli: I have been around multiple ponds together. Swiss Army knife is an understatement. Dan, my partner, is the same, but our ven diagrams are interesting. we overlap just enough.
Mark Donatelli: but we're very different, which means we bring a lot. So, there's a lot of stuff we can talk about there. the agency deck is in there. lot of words. Again, this is a more of our manifesto level type thing. We're still working through the content specifically, but the way that all that essentially those chicklets are verbs, those are the things that we do.  And so, in a lot of ways, those things aren't linear, as you can imagine. They're not linear. you don't have to do whatever first. you can hop around in there. The consulting deck is kind of the same way. The consulting deck, again, is super broad.
Mark Donatelli: 
Mark Donatelli: If you think about what we were doing at the consulting deck and the agency deck, those two decks in total are probably almost everything we were doing at Oggov and then some. this is basically Oglev one type of stuff. in the credentials deck, we have a bunch of stuff in there about the work we've done with clients. We only have one real case study that's been formatted and published. It's on the website that was for Do you remember Andrew Weiselberg from Oggov?
Tom Hutchison: Then yeah, the name was familiar, but I couldn't place.
Mark Donatelli: He was the account guy on Citizens Bank.
Mark Donatelli: 
Mark Donatelli: And I know you did some marketing automation work for Citizens Bank, like some design something or other, I don't know,…
Tom Hutchison: Yeah, it was
Mark Donatelli: a million years ago, Yeah. So, Andrew has been our client multiple times over the last several years.
Tom Hutchison: 
Mark Donatelli: He's on the brand side now.
Tom Hutchison: Mhm. Thanks.
Mark Donatelli: We've worked for him multiple places doing paid search, paid social, in-house agency stuff for him.
Mark Donatelli: 
Mark Donatelli: building Salesforce automation stuff, email templates,…
00:05:00
Mark Donatelli: taking Salesforce and CDP like segment and taking third party all this stuff like getting into a data warehouse, bringing the Shopify data in, matching it up so we can do anything. we have some offshore resources which They're time zone friendly they're south. so we have a partner we can go that direction with headed south.
Tom Hutchison: Yeah. Mhm.
Tom Hutchison: 
Mark Donatelli: If we need work obviously you have resources in Ukraine.
Mark Donatelli: 
Mark Donatelli: So, I'm guessing unless we're going around them or…
Tom Hutchison: Not enough.
Tom Hutchison: No. Mhm. Yeah.
Mark Donatelli: we're going to supplement we would want to get obviously all kinds of approvals for all that to make sure we don't piss anybody off. But clearly, if it comes to building a prototype or whatever we're going to do, Dan actually built my partner, he just built two apps for a project we're on. his brother works for us sometimes. his brother works for he's in the data science team at Uber and he just is a beast just can't get enough work kind of guy the type. he just wants to work continuously.
Mark Donatelli: 
Mark Donatelli: And so we could prototype something like you talked about this interface for whatever. we can show you and we'll get to that at some point, but I'll have Dan walk you through it. But it's super lightweight, Java just super interactivity that allows again if you're looking for something super light to put in front of these people like it maybe a way we can start prototyping stuff pretty quickly.
Tom Hutchison: No, I get it. Yeah.
Mark Donatelli: You know what I mean? So that whole control panel stuff's interesting to us. in the consulting side I know I was talking about the decks, on the consulting side that work in there.
Mark Donatelli: 
Mark Donatelli: So again, we've been trying to become more focused, And so part of our renewed focus is what is in those decks, believe it or not. and so we have a consulting business, we have an agency business. and the consulting business is One of the lines in that's interesting for you guys, we would probably draw from is The data factory practice is a lot of what we did in Oggov. It's data strategy. It's data sourcing. it's building the data layer like how do you build the identity graph and how do you do all that stuff right? how do you build a data center of excellence so a bunch of those things are going to light up for you guys…
Tom Hutchison: Yeah. Yeah.
Mark Donatelli: because you're in the So data factory is really interesting there because that's where the product management stuff comes in.
Mark Donatelli: How do you build a data product? How do you merchandise it? How do you price it? And I consider a managed service or a headless API or data as a service. All that's when I say product, I mean it's all the same and that, right? so yeah you guys are definitely in this data as a service data product manage service API scoring whatever vehicle it is like all of that all that fits into our data factory practice pretty cleanly.
Mark Donatelli: the other parts of the consulting practice, the marketing transformation there's probably a light version of that for your clients perhaps. hey, this is how you should be thinking about raising, how you think strategically about fundraising in the 21st century. there's probably a pitch there we might help you work on how to position that pitch. that's where that would come in. it would be about you transforming how you get customers and talk about it and some of that could roll through to the client side I guess. customer centricity that's all first party data appending matching segmentation profiling like that's all the stuff you guys do.
Mark Donatelli: 
Mark Donatelli: to some degree. and so looking at what your offer is there specifically, what are the inputs, what does the client provide, what do you do to it, what's the value ad that's created,…
Tom Hutchison: What's up? Nothing.
Mark Donatelli: what comes out, what does the client pay for it, how's that calculated, that whole sequence of what's great about the transcript too, I know you're writing because I like to write when I'm listening also. you'll get a transcript of this as well. So you'll have all these words. so I think the customer centricity is interesting because the spirit of that ultimately this would all manifest on the agency side but I think because we do all the same stuff on the agency side but we just do it for the client as a service. it's all semantics I guess so there's some customer centricity concepts there that are interesting that may look at what you're doing, how you're doing it.
00:10:00
Mark Donatelli: 
Mark Donatelli: Maybe there's some gaps in the data we're sourcing. I know the Allesco people I know Peterman and what's his f*** or…
Tom Hutchison: 
Mark Donatelli: I'm sorry, what's this dude over at Allesco or buddies way back those guys that known each other forever. not to say anything bad about the Allesco guys. I lived in Fort Myers. that's where I came into the data business. everybody knows everybody in that town. they're probably getting a sweet deal. I don't think the data is probably not great, but they're probably getting a really good deal on it.
Tom Hutchison: Yeah. It's commodity data.
Tom Hutchison: I don't really give a s***. I mean,…
Mark Donatelli: So, with that said though, there's probably a way to figure out what data does matter in your world most and then try to upscale the sourcing on that.
Tom Hutchison: Mhm. Yeah. Mhm.
Mark Donatelli: 
Mark Donatelli: And that's super easy, I have a list of 150 places We'll just get the list and we'll just go call them. we'll build data requirements. We'll just figure, there's a way we could do that. and that feeds on the data practice. know. I think there's the overall strategy of the business. I know that some of that is going to be obviously influenced more at the investor level because they have a plan. They have the way I was reading about it like I went and looked at all the press releases at Behringer and who they've bought and what they say about it and…
Tom Hutchison: Yeah.
Mark Donatelli: they're viewing these as funds they're building a fund they raise money for a fund for advertising technology fund and then they go out and they try to spend the money and whatnot.
Mark Donatelli: It's like the question is what is Behingers? we don't know what their split is. We don't know if they're minority. I don't know any of those answers, but all that strategy stuff is obviously up beyond where you're being asked to contribute. So I would probably just set all that aside for now. as we get some wins, ask some of the right questions. I suspect Matt and I will have that conversation at some point to say, "Listen, What are you trying to do?
Tom Hutchison: 
Mark Donatelli: Are you trying to make it to a 100 million and then cash out 100 million at a 100 million at a 3x, or what's the goal?
Tom Hutchison: What? Right.
Mark Donatelli: What are you trying to do?" Because if we understand what you're trying to do, we can help you build the business to have a revenue and profit profile.
Mark Donatelli: 
Mark Donatelli: that meets the criteria. So for example, you wouldn't want to grow the services revenue…
Tom Hutchison: And that's…
Mark Donatelli: because as much as you want to grow product revenue,…
Tom Hutchison: why Yeah.
Mark Donatelli: you want to have this product revenue and…
Tom Hutchison: That's why platform play Yeah.
Mark Donatelli: margin 100% true.
Tom Hutchison: The platform play is really about value expansion…
Mark Donatelli: 100% true. deafly somehow I'm going to keep this thing rolling.
Tom Hutchison: because we could grow services all day long and nobody would give a s mean, at the end of the day,…
Mark Donatelli: I'm going to switch to my earbud and start getting in the car. I want you to let's just keep talking. Let's talk about so we talked about so that's kind of how I see all this stuff fits.
Mark Donatelli: I think a bunch of ways that it's a matter of just understanding…
Tom Hutchison: Yeah. Yeah.
Mark Donatelli: what are the current discrete revenue flows in the business and each of those discrete revenue flows is essentially a value chain right there's a salesperson does this do that then the customer has something there's acuity does something, someone else does something,…
Mark Donatelli: then someone else does something and then it's in the market and then the money gets donated. how does that get track?
Mark Donatelli: start me down that process of what you understand so far to be that business. Hey
Tom Hutchison: All right.
Tom Hutchison: So yeah, I've been thinking about this over the weekend. So, there are three streams that I would like to follow.  one of which I want to walk you through the Perry process because that's where everybody's strategic focus is right now and there are some of your offerings fit into that.
00:15:00
Tom Hutchison: So, I'm thinking about short-term easy wins. supply assessment, value creation, unified taxonomy. Those are things that we can get you established within Veridata Holdings. the overall company, not just the Veridata of Matt and Mike.
Mark Donatelli: 
Tom Hutchison: 
Mark Donatelli: Hold on.
Tom Hutchison: And…
Mark Donatelli: Hold on.
Tom Hutchison: right you hear me twice.
Mark Donatelli: Hold on one second. if I can mute this. that might help. I can hear That's good. Keep the No, I hear you good. And the meeting is transcribing, so that's cool. So, let's see if I can get in the car without hanging up and on.
Mark Donatelli: we'll all be set. So, back up for one second. I know it was transcribing that, but as I was switching, I didn't hear I know you'd mentioned it's probably See if you can back up a second. on.
Tom Hutchison: Three streams of activity for us.
Mark Donatelli: Yep. Thank you.
Tom Hutchison: One I want to introduce you to the Perry process and there are some offerings that you've got today that fit in with specifically supply assessment, value creation, and unified t taxonomy. Those solve some business problems that we have specific to Perry right now. and so also kind of ancillary to that I know that we've walked away from business around risk mitigation and technology selection. So the first thing I want to do is kind of adopt this thing which didn't have any definition to it but Matt's idea of data concierge.
Tom Hutchison: I want us to build out the data concier service around at least those five things that will give the salespeople things to go out and…
Mark Donatelli: 
Tom Hutchison: sell and start establishing the relationship. start establishing your reputation and…
Mark Donatelli: What do you think?
Tom Hutchison: verata holdings. Second thing.
Mark Donatelli: Go ahead.
Tom Hutchison: No, go ahead.
Mark Donatelli: I was going to say, what do you think when you guys are working with these clients that are doing these service with you,…
Tom Hutchison: So, yeah.
Mark Donatelli: how much are they spending with you guys? I mean, obviously you have that one giant client. but I mean what do you think if there's an opportunity here? are these $5,000 little add-on services or Are they more than that? what do you think is it a technical thing?
Mark Donatelli: 
Mark Donatelli: Is it okay?
Tom Hutchison: Yeah. …
Tom Hutchison: these are the least technical clients that you're going to have. Period. By a long shot. and they're nonprofits, so they don't have a lot of money to spend. So they're cheap,…
Mark Donatelli: Okay.
Tom Hutchison: but they will spend money if we can show them that the value is there. So it's going to be less than a hundred,…
Tom Hutchison: but more than 10,000.
Mark Donatelli: Okay. Yeah. Yeah.
Tom Hutchison: And at the end of the day, I barely care because what I want is to get your reputation established within the company. At that point, what I want is to start inserting you as a resource for Faircom New York and New River.
Mark Donatelli: 
Tom Hutchison: So when they have things that they can't do,…
Mark Donatelli: Yeah, sure.
Tom Hutchison: and there's a lot and they have overflow work that they can't get to in the agency side of the business, I want you to be the to group that they open up to. establish the reputation first.
Mark Donatelli: Sound good.
Tom Hutchison: then establish you as the to people to help shore up the agencies. Not related to those. when I walk you through the Perry process, I want to also walk you through some wireframes for what I want to do to make the whole thing seem like a platform. It's not going to be a platform. let's acknowledge the technical shortcomings of the organization is not going to be a platform.
00:20:00
Mark Donatelli: 
Tom Hutchison: It's probably going to be point solutions that feed up into a common user interface. But that's okay. We're not there yet.
Mark Donatelli: Look, a platform by definition,…
Mark Donatelli: …
Mark Donatelli: a platform is just a common flow. it doesn't have to be integrated per se for now. Yeah.
Tom Hutchison: Yeah, for now.
Tom Hutchison: Yeah, ideally you would want your platform to have one data layer, one set of security, one that's not going to happen.  I don't think it has to happen and that's really talking more of a theoretical world.  So the cornerstone so there are a bunch of things that we create today that have a user interface although they're not great tackling those one by one but the thing that's going to differentiate us in the marketplace is this tool that takes the prescriptive analytics
Mark Donatelli: 
Tom Hutchison: 
Tom Hutchison: that the teams create and interpret that for a nonanalytical user.
Mark Donatelli: So just to pause there for a second.
Mark Donatelli: So when we talk about the model they create. So you're referring or the prescriptive thing that you create. You're saying they produce a set of deciles or…
Mark Donatelli: cells or what is the thing they produce? What is the output? Yeah.
Tom Hutchison: It's a lot of different outputs.
Tom Hutchison: Sometimes cil sometimes it's a flag. What Matt wants to get to is you drop a donor database in the top of this thing and it does a whole bunch of stuff and it pops out. You need to break this million people into 10 cells. These three get These two get a message that is focused around, a sad emotional experience.
Mark Donatelli: Yep.
Tom Hutchison: These three have nothing but numbers in them.  And these two are wild cards where we're trying things we tried before. So that whole process of getting the data doing all those analytics and then the interpretation of the analytics. I think that that's the way he kind of thinks about Perry is it and it's how he thinks about the agencies too. I don't know how much he cares about the actual creative part.  He thinks about the agencies as the people who are taking his analytics and interpreting from them for the client. And what I want to add to that is a user interface that lets you see it. Because right now you've got all these analytics that happen. It's a black box. Nobody understands what the output is. Nobody understands why they should care.
Tom Hutchison: 
Tom Hutchison: So even if it is not used on a day-to-day basis, it is at the very least a sales tool that lets people understand what they're getting out of these analytics. Even if the actual production work is all automated and behind the scenes, I wouldn't even go there.
Mark Donatelli: So, how I mean obviously there's some well in the middle right from a training perspective like the ability for Perry or it's a language model I assume with some other stuff mixed in there.
Tom Hutchison: No, if they're using an LLM, they haven't told me which one it is.
Mark Donatelli: Perry then it's a recommendation engine. what's the
Mark Donatelli: 
Tom Hutchison: Yeah. at the end of the day. Yep.
Mark Donatelli: Yeah,…
Mark Donatelli: so you're going to have some inputs, There's some weighted variables that have to go in. how standard we've all done data pen jobs, We know that the sensitivity of matching is important. So when we say dump a customer database in there,…
00:25:00
Tom Hutchison: Mhm.  Yeah. Heat.
Mark Donatelli: there's a lot to unpack there.
Mark Donatelli: you know what I mean? but yeah, I don't know. we're doing this right now. I mean, and Dan will tell you more about this, but he built two apps this past week or past month, I guess, a better way of putting it. He showed them to me this past week. We're in this Goldman Sachs 10,000 small businesses program for our agent for our agency because we've been in business for a while, but we're starting this agency.  So we entered this small business program with Goldman Sachs as the agency. So basically Dan's getting an MBA or what almost out of this we're going through this program. and so on the agency side is that one of the things we do in there is we do analytics.
Tom Hutchison: Yeah.  Mhm.
Mark Donatelli: to do data visualization dashboard some of the stuff you're talking about and I think that we've been doing this for a couple of clients we started out we were doing it originally first couple years and even when I was at hive when I was at hive before I started simply I was using Tableau PowerBI to do a lot of these things Tableau and PowerBI
Mark Donatelli: 
Mark Donatelli: I both have an AI layer in them that tries to make recommendations or that in Microsoft PowerBI you can ask if it understands your taxonomy of your data you can ask it questions and say hey it'll say hey make me a chart for show me but again it's a little clunky I think it's getting better so with that in mind now all of those are not like they're just expensive and they're kind limited based on what you're paying for. and so we have moved away from all those tools. for our clients are working purely off of SQL databases and R and Python and…
Tom Hutchison: Yeah. Yeah.
Mark Donatelli: and Java JavaScript and some other stuff.
Mark Donatelli: 
Mark Donatelli: Some JavaScript packages for charts and stuff. …
Tom Hutchison: So our develop
Mark Donatelli: so we have a bunch of ways we could help. Yeah. this is something that seems like it'd be easy enough.
Tom Hutchison: Yeah, our guys use React in D3.
Mark Donatelli: I don't know. Yeah. Yeah. Yeah.
Tom Hutchison: I mean, pretty standard stuff there's nothing exotic going on in Ukraine. but the other thing is that the interface that I want just because the recommendations get spit out doesn't mean a customer is going to take them. I also want them to be able to go in and make their own changes too. And we've got a production database where we manage all of our solutions. So this will interact with the production database.
Tom Hutchison: 
Tom Hutchison: And that's another area where we might talk. I'm not sure. I like the way the production database is being put together. but everybody has work they need to get done right now and so nobody wants to change a direction. And I don't know that I've got a better alternative for them yet.
Mark Donatelli: 
Tom Hutchison: So, we usually SharePoint is…
Mark Donatelli: Do you use …
Mark Donatelli: what was I going to say? what's that?
Tom Hutchison: what they're using to build the production database.
Mark Donatelli: Okay.
Mark Donatelli: That's interesting choice. I too like to live dangerously. Yeah. So basically production.
Tom Hutchison: I have asked pointed questions and…
Tom Hutchison: people have not appreciated it. So I am treading lightly but I'm like what you do you doing what? so yeah no it's mostly informing the next step in the process that the step is I mean look and…
Mark Donatelli: 
Mark Donatelli: So when we say production, they're using that to push around notifications, Are they actually pushing data around with rules in there? It's no harm, no file. It uses Microsoft Directory. It's probably how they manage all that stuff. But yeah, it's not great for sure.
00:30:00
Tom Hutchison: part Perry is also capturing a whole boatload of metadata about the creative. And so when I come to them and I say there's 400 new data elements that I want you to start managing or is it at…
Mark Donatelli: They freak out.
Tom Hutchison: At what point does it get to be too much?
Mark Donatelli: 
Tom Hutchison: And truthfully, once we get started, it's probably going to be 1,400 data elements that are potentially capturable for any particular treatment that we do.
Mark Donatelli: Yes. Yeah.
Mark Donatelli: Are you using a proprietary ID graph? how do you manage an identity?
Tom Hutchison: Merge purge
Mark Donatelli: Yeah. So yeah,…
Tom Hutchison: Dude, this is Axium 2001.
Tom Hutchison: I mean, just put yourself in 2001. that's where we're at. No, there's not an identity graph. There may be So, there's some infrastructure that we've got that for some reason I can't learn about even…
Mark Donatelli: there it goes.
Mark Donatelli: 
Tom Hutchison: though I've asked about it called the charity database and…
Mark Donatelli: Yeah. Yeah.
Tom Hutchison: it's where we take basically it's a big promotion history table for all of our customers and response history table for all of our customers. So we can see across kind of everybody that we do business with who they've mailed and who they've gotten responses from. The way they talk,…
Mark Donatelli: So there's a lot of poor man's ways to do it.
Tom Hutchison: it sounds like there's an identity graph for that, but I don't know if they're just creating a unique identifier out of their merge purge. I don't think it's a commercial identity graph, but Yeah. Yeah.
Mark Donatelli: I mean, the way I've been doing it lately for man is when on the third party data sources, there's a household ID and an individual ID in there. unless they're trying to transport that ID to some other source, as long as it's unique,…
Tom Hutchison: 
Mark Donatelli: you could take the 14digit zip code or whatever. there's a delivery point ID and…
Tom Hutchison: Yeah. Yeah.
Mark Donatelli: they could be using that to do aggregate, but then when names change, they break it. There's a lot of ways you could do it from the old info or you know what I'm saying.
Mark Donatelli: 
Mark Donatelli: So yeah, yeah, so that's probably an opportunity for them to like…
Mark Donatelli: because again if they have a third party data source if they're considering that to be the truth of the mailable universe of the target universe because this is all predominantly, right? So it's all offline meaning postal or is it email too? Okay. So, direct mail, postal. So, yeah. So, it's all offline.
Tom Hutchison: Yeah. mostly direct mail. Yeah.
Tom Hutchison: 
Mark Donatelli: So, they've got to have some version of the truth. They've got the NCOA or whatever. so they have some version of the truth. I'm sure that in their minds to them that's the identity graph. that's the truth system of record.
Mark Donatelli: 
Mark Donatelli: And then they attach all the promotion history. There's got to be an ID in there somewhere. the first time they see a last name at a delivery point, there's got to be an ID or they concatenate the fields or, there's some concatenation or something that takes place to do what you're talking about. have they done any analysis on that aggregate data set?
Tom Hutchison: Yeah. Yeah,…
Tom Hutchison: but they're not great on documentation. There's been a lot of build it because we need it right now and until it breaks, I'm not going to worry about it. So, Yeah.
Mark Donatelli: I assume that's what feeds the future scoring, right? That's how they do it.
Tom Hutchison: I mean, yeah, you're right. that's what they use for the scoring. And, there's a lot of insights that come out of that. they don't talk about those insights ly very much,…
Mark Donatelli: 
00:35:00
Tom Hutchison: which is interesting. I think it's a marketing opportunity that's missed. Yeah. So they feel so the number of companies contributing to this is about 200.
Mark Donatelli: Yes, I agree.
Mark Donatelli: They should be no different than there's a bunch of companies in the Finn data space, the transaction data people, Yeah, they're on CNBC all the time or whatever talking about, yeah, this, consumer trends that. These guys should be talking about donate, fundraising trends all the time. There should be a quarterly report.
Tom Hutchison: And so there is also the feeling that it's not big enough to give an industryworthy story and I'm like no one else is. Yeah.
Mark Donatelli: 
Mark Donatelli: Look, all you got to do is footnote it because then if they did a survey, what they do is you could do a 10 question survey amongst the 200 customers, Do a 10 question survey. take the aggregate data, show them some stuff, ask them five more questions about the data. And you've got literally do that every quarter and…
Tom Hutchison: 
Mark Donatelli: offer them some fake discount for doing the survey.
Tom Hutchison: Yeah. Mhm.
Mark Donatelli: You know what I mean? And you get people to do it. and then you're like, "Okay, the N equals 158, which is five more than last quarter, or it's four less than, you just got to footnote it." And as long as the numbers are there, it doesn't matter.
Mark Donatelli: 
Mark Donatelli: I published research of 25 people before doesn't matter.
Tom Hutchison: Yeah. No,…
Mark Donatelli: You just gota be transparent about it,
Tom Hutchison: I'm with you.
Mark Donatelli: So yeah, I like that idea a lot. I think that's do you think there's an opportunity in so this data again they have responder who was mailed who responded they probably have some understanding of there's probably a bunch of metadata that goes with that right the amount of the type of gift the channel the way they paid the like are you guys involved beyond delivering the piece or is it you guys collect the
Mark Donatelli: funny too, That's what I didn't know the word. Okay, that's they being the client CRM or…
Tom Hutchison: we'll get the donation data back from usually through their CRM. yeah,…
Mark Donatelli: through So then when that happens when that Okay.
Tom Hutchison: the didn't share that.
Mark Donatelli: 
Mark Donatelli: So are they contractually obligated to share that data and is it just discreetly they're not okay there's an opportunity right to ask for that again fake discounts work do so yeah that's something there I think that there may be an opportunity Then to add on from a digital perspective,…
Tom Hutchison: We ask for it and we get it from a lot of clients because they view us as partners but I don't think we get it for everybody.
Mark Donatelli: think about digital here and we think about omni channel or start crossing over. you might provide the landing page for again these le less sophisticated people.
Mark Donatelli: 
Mark Donatelli: It's pretty easy to say, "Hey, as part of your campaign, we'll put a QR code on it and we can send them to a landing page or there's some way you have to insert yourself in a digital response." So you got again that's not something I'm not going to solve for right now but there's probably a way to throw on the board somewhere hey is there an opportunity to insert you guys in the digital response so that you can track and…
Tom Hutchison: Yeah. Mhm.
Mark Donatelli: again that's the value proposition. Hey Mr. client, you don't have to now run this job and pull this data and Send them through this URL or use this QR code or there's ways you can do variable data printing now and has been for a long time and Kai Kaiser knows this.
Mark Donatelli: 
Mark Donatelli: This is how I bought my first Mercedes at AcuData is I found a guy that was doing postcards and I set him up with an API to the Axiom info basease and I'm like, "Hey man, let's write this query. we're going to find owner occupied single family homes based on a rooftop radius of this, blah blah blah blah blah. We're going to write this API and we're going to pump out 500 postcards every time a house goes on the market." And I made hundreds of thousands of dollars in commission reselling Axiom data on something so simple.
00:40:00
Tom Hutchison: Yeah. Yeah.  Right.
Mark Donatelli: You got to make it that's where these guys you create these simple little products for them. hey donor expansion campaigns as an idea for you. we want to mail your neighbors of your best donors. Just mail the people next door.
Mark Donatelli: Hey, did you know your neighbor recently donated to XYZ cause it's an easy way for you to add volume right or again geograph there's a whole bunch of ways of do geographic stuff to where you're like this bridges into the agency side right where we're like hey if there's geographic concentration of that mailing you should also do a geographic sweep on Facebook  or on Pinterest or on put a picture of the postcode. Super simple. You've already got the reshape the artwork a little bit, continue on with your print flow, right? We'll just branch off. take that artwork, traffic it on paid media on
Tom Hutchison: And there's some of that that goes on. So there's a lady at Faircom named Shelley Hudson…
Mark Donatelli: 
Tom Hutchison: who is vice president of digital.
Mark Donatelli: Okay.
Tom Hutchison: I think when they say digital they mean email because I asked her if a particular client used a CDP and she was like what's a CDP?
Mark Donatelli: So, we'll find out.
Mark Donatelli: But these are all like these little flows that we're going to want to document these flows again not right now. I mean I'm just trying to write a proposal here. So I think that'll be part of the scope somehow is just we got to understand all these flows so that we can plug in the right services.
Tom Hutchison: Yeah. Yeah.
Mark Donatelli: 
Mark Donatelli: I think that so there's a way to capture more channels more digital that way by adding on through geography. Again, if you guys are building these prescriptive things that say, "Hey, here's segment which is for the segment A emotional plea has 5,000 names in it. If you take those 5,000 names and…
Tom Hutchison: Mhm. Yeah.
Mark Donatelli: upload them into Facebook and build a custom audience, now you can target again people that do lookalikes.
Mark Donatelli: 
Mark Donatelli: Now we're doing Facebook lookalike targeting. You can do Google DV 360. You can do lookalike targeting there. you could do literally getting crazy now. you can do connected TV, …
Mark Donatelli: you could have a Sarah McGlaughlin soundtrack or something here.
Tom Hutchison: And there's I think we've Yeah,…
Tom Hutchison: I think there have been a couple of test projects using connected TV. I think this is one of those areas where I think everybody sees an opportunity, but they don't know how big it's going to be. And I'm like, all TV is going to be CT CV soon. So we should get in front of …
Mark Donatelli: A lot of waste there, a lot of fraud there. but yeah,…
Tom Hutchison: also I mean remember we're making a boatload of money on direct mail print production.  So, one of the things I'm trying to do is keep direct mail at the center of it, but let's do a test to see if you do Facebook ads for a week before the direct mail is going to be delivered, Does it affect response if you do Facebook the week after the direct mail hits?
Tom Hutchison: 
Tom Hutchison: And there's just a bunch of bonehead stuff that is opportunity for us.
Mark Donatelli: Yes, I'm switching. East country.
00:45:00
Mark Donatelli: 
Mark Donatelli: Did that work? Totally worked.
Tom Hutchison: That was smooth.
Mark Donatelli: That was actually pretty smooth.
Tom Hutchison: That was smooth.
Mark Donatelli: I think if I probably could have turned my camera off and tricked You probably would never know. so no. Yeah. So, I think because what I'm picturing is I think that there's a bunch of ways that part of what we're going to find is we're going to find say 20 opportunities. there's going to be things that are immediately …
Tom Hutchison: 
Mark Donatelli: hey, let's write up a one pager and immediately put this stuff in front of the agency people so they can make it happen, They can call us. Then there's things that we got to work on a little bit or there's a longer list of things like, hey, out of this longer list of things we got to kind of prioritize and see where help is needed or not. …
Tom Hutchison: What? Mhm.
Mark Donatelli: but yeah, I think so.
Mark Donatelli: But yeah, there's definitely understanding how they frame digital is really going to be important. because again as you get into this idea that Perry is going to be this helper or assistant that's going to help with what they're trying to understand or do. anything that we start to provide as a service or as an add-on is a candidate to ultimately get automated,…
Tom Hutchison: Damn it.
Tom Hutchison: Right. No. Yeah.
Mark Donatelli: which is great. And so, there's no reason why that this thing shouldn't be able to do a lot.
Mark Donatelli: And again, we want to just be focused though because I did some work with remember JP Buley? So, I did some work for one of JP's clients. Cox. So, Cox has cable, internet, phone, car dealerships. they own Kelly Blue Book. they've got crazy diversified business, and one thing that they were looking at is, trying to understand what is the…
Tom Hutchison: 
Mark Donatelli: what is this suite of marketing services that we can offer to small businesses,…
Tom Hutchison: Mhm. Yeah.
Mark Donatelli: all self-service stuff.
Mark Donatelli: 
Mark Donatelli: And so we built some prototypes where they would enter in their URL. we would take their URL through our interface behind the scenes. We'd send it to Semrush, get a report.
Tom Hutchison: Mhm.  Yeah.
Mark Donatelli: We could parse that report, get insights, streamline recommendations for them of you should do these things on your website and we'd find out other things about so there's all kinds of ways that we can automate these recommendations but then what becomes powerful is when you can say okay do it and then you want to click the button if they can say add Facebook to this campaign they should be able to tick a box and then somebody at Fairchild should be like s*** I gotta add Facebook to this campaign and then they got to add Facebook to the campaign.
Mark Donatelli: 
Mark Donatelli: But then clearly we could do that or then clearly you could also automate that at some point eventually because all of these companies have APIs right now we're in the process of we use Zoho CRM and…
Tom Hutchison: Mhm.
Mark Donatelli: we're starting out really push data around in there using templates with emails and stuff. So there's all kinds of stuff that these guys you could really run you could create packaged omni channel campaigns. here's a religious organization quarterly plea blah blah blah blah blah.
Mark Donatelli: 
Mark Donatelli: And in this package, you get a quarterly postcard and you get Facebook ads, blah blah blah, and it only costs X, make it an easy sale.
Mark Donatelli: And someone buys a package of these services,
Tom Hutchison: Yeah. The other thing to keep in mind and…
Tom Hutchison: the reason that I want to focus on some of those data services early on is how backwards things are in this industry. So we don't use any APIs So if we get data from a client, even if they have a CRM that offers an API, we don't use it. So there's a lot of sort of behind the scenes work that's going to have to happen too to modernize Veradata infrastructure. because we are FTP CSV files from one place to another, right?
00:50:00
Tom Hutchison: 2001 just from,…
Mark Donatelli: 
Mark Donatelli: I think but in terms of right so here's a question for you.
Tom Hutchison: from Amazon where everything had to be an API or you couldn't launch it.  Yeah.
Mark Donatelli: This is a serious question. This is one of these obstacle slow down for yellow lights. I remember Mahan Kalsa. So remember let's not play all that stuff. slowing down for So a yellow light is on the infrastructure right?
Mark Donatelli: So I know for a fact that when I was at ACU data or I was even at Axiom to some degree at Axiom I knew that depending on which system it was if there were Little Rock or Conway based systems rather if there were Conway based systems and there were team delivery teams there that own those systems I knew there was a certain way I had to go to get things kind of done right. and I knew who to work with. on the list key was run out of the Ukraine and so that was a separate process that supported that system and then again they didn't work for me. I wasn't like in your shoes. I was kind of in your shoes, right?
Mark Donatelli: they didn't work for me, but they directly controlled the flow of change management into the system. And so I had to learn how to work with them. and they were very hesitant to do stuff. they the way that I got the API working the way I wanted it working was I put so many user interface requirements on them that they're like, "f*** this. Build it yourself.
Mark Donatelli: 
Mark Donatelli: And I'm like, give me an API and I will. And so I think you've got to be able to figure out are they going to ultimately acquies? Does and who's really in charge? is Peterman again I assume Peterman I don't know if they're equal partners he and Matt or not. but who really decides? if you say, "Hey," and we're not saying there's some big whisbang infrastructure overhaul.
Mark Donatelli: That's not what You're just suggesting there needs to be some incremental movement towards a more automated distribution,…
Tom Hutchison: Yeah. Automated.
Tom Hutchison: Yeah. Yeah.
Mark Donatelli: process. so that's a whole how much of a risk is that?
Mark Donatelli: And I guess is where it's a long way of asking how much of a risk is that? how you haven't been there that long, but do you sense that they'll make a tough decision someday or do you think that if it gets that they're really more focused on getting to the revenue profile they need to exit more so than they are building the best fundraising technology capability?  Yep.
Tom Hutchison: investments. I mean, I am basically an investment for them. it feels like there's a diffusion of responsibility cuz you've got Michael and Matt but Svet Lana is the one who makes the technical decisions because she's the chief analytics officer and she owns all the technical teams
Tom Hutchison: And I haven't seen them all together enough to understand the relationships.
Mark Donatelli: 
00:55:00
Mark Donatelli: …
Tom Hutchison: So I don't know.
Mark Donatelli: she has all the development everything.
Tom Hutchison: Yeah. Yeah.
Mark Donatelli: So, she's basically running the Ukrainian operation.
Tom Hutchison: Yeah. No.
Mark Donatelli: So, there's nobody in Ukraine higher than her. Is she in Ukraine or is she out of Ukraine?
Tom Hutchison: She lives in Romania now,…
Mark Donatelli: But nobody in Europe is above her basic. Okay.
Tom Hutchison: but I think she is No. No, I don't know.
Mark Donatelli: 
Mark Donatelli: Do you know when those guys went over there last? I assume that the technical team is all dispersed probably. yeah.
Tom Hutchison: Yeah, every Looks like everybody's homebased. If there's an office, I don't think anybody goes to it.
Mark Donatelli: What's the COO's name again?
Tom Hutchison: Mike Kinsky,…
Mark Donatelli: Yeah. I got them written down somewhere else, too. I'll just write it in here again. so yeah, I think that it's a reasonable risk, I think, because the question is going to be like you don't want to build a big thing that's never going to get done or you don't want to try to build a big thing that's never going to get done.
Tom Hutchison: Fine. Mhm.
Mark Donatelli: 
Mark Donatelli: you'd rather be pragmatic and help them achieve their goal. But you probably clarification on The actual goal probably is get to the exit point knowing that along the way you're going to have to do some shoring up. But no one has said we want to be the premier fundraising blah.
Tom Hutchison: 
Tom Hutchison: Yeah, but I mean that's marketing I mean, are they looking to displace innov Chad Engelgal they're a competitor.
Mark Donatelli: So they're a competitor. All right.
Tom Hutchison: They don't talk about them like a competitor which I think is really interesting. And then there's an agency conglomerate more is their URL. who is the biggest competitor on the agency?
Mark Donatelli: I'm good time, You on time? I'm good on time. yeah, they're part of a holding company, right? More the WP.
Tom Hutchison: Yeah. …
Tom Hutchison: they Yeah.
Mark Donatelli: And do they want to buy us?
Tom Hutchison: So, they've been out buying up a whole bunch of smaller agencies So, it's interesting. So, when everybody's talking about I don't know.
Mark Donatelli: They could. Maybe they will when we're done.
Tom Hutchison: Yeah. I mean,…
Mark Donatelli: All right. Yep.
Tom Hutchison: it would make as much sense as anything. all right, let's talk co-op for a second.  We have a co-op and so when people talk about competitors they often talk about the other co-ops specifically Missionwired and Wland. There's one more I can't think of it off the top of my head right now. Matt doesn't want to be in the co-op business to be a co-op.
Tom Hutchison: He wants to be in the co-op business to get data that he can aggregate for analytics.
Mark Donatelli: Mhm. I'm sure
Tom Hutchison: So the co- there's no user interface. You can't go query the co-op to see how many records you could go back fill your campaign with. there's no way to go figure out what's in the co-op. Basically, if somebody wants to buy data from the co-op, it's gonna go through Matt. And I'm not sure, but I think Matt actually sits down and codes the query in the co-op to make one thing that I'm turning over in my head is do we figure something out that is a competitive differentiator for the co-op and…
01:00:00
Mark Donatelli: 
Tom Hutchison: get into the co-op  business in a real way? Or do we shut the f** about it? And
Mark Donatelli: It depends on…
Mark Donatelli: how much it's costing or is it dragging on infrastructure? Is it dragging on resources? Is it purely the value it provides in data? must outweigh the limited voice it gets. I don't know. Is that Yes.
Tom Hutchison: I assume so. I mean, in my mind if the co-op is there for analytics, the co-op at least needs to pay for itself. Even if the value is coming from the analytics on the back side,…
Mark Donatelli: 
Tom Hutchison: I don't give a crap. But the co-op needs to pay for itself, and I don't know if it does or not. about 200.
Mark Donatelli: How many members are there?
Mark Donatelli: So, they are all opted in co-op members,…
Tom Hutchison: Yep. Yeah.
Mark Donatelli: and these are the same 200 you talked about before. H.
Tom Hutchison: And so when I ask questions "Is the charity database the same thing as the co-op database?"  I never get a straight answer on that.  So my sense is that people have taken some technical shortcuts and don't want to admit it. Yeah.
Mark Donatelli: 
Mark Donatelli: So the co-op I'm again obviously one of the action items we would look at down the line if we get there would be ultimately like what does that actually look like data dictionary wise
Tom Hutchison: Excellent.
Mark Donatelli: because I think the members there's historical charity database may have historical the co-op data may just be active there could be a bunch of ways to demark that I
Mark Donatelli: 
Mark Donatelli: I ran into this down in Brazil when I was at Axiom. There was a database company down there, a co-op that we worked with and they had some weird way of demarking between what was the analytics industry database versus what was the active live co-op freshest version, things things got moved out of the active file regularly into the historical file and so the members could only access the current file as part of it…
Tom Hutchison: 
Mark Donatelli: unless they paid a subscription fee to get to the historical.
Tom Hutchison: Yeah. Mhm.
Mark Donatelli: So there's a bunch of ways that we might be able to entice him to explore. This is again the data factory line in the consulting deck.
Mark Donatelli: 
Mark Donatelli: Is the data co-op a business or not? Yes or no? Is it a business or is it a function of the supply chain? Right? That's a good question,…
Mark Donatelli: right, to ask them. and that will dictate how you go about if it's a business, there are ways that you could monetize and add pure profit to the business if you were to monetize this in a compliant way. Meaning you could upsell it to the same members. You could tear their own tier their access, benchmarking services. Then you start bringing in other third party data and provide that in there and then benchmark it against people love that kind of stuff. You could feed that. I assume this is what gets fed into Perry, So then All right.
Tom Hutchison: Thank you. Yeah.
Tom Hutchison: Yeah. Yeah.
Mark Donatelli: 
Mark Donatelli: So you were talking so W mission wired and Wland co-op.
Tom Hutchison: Yeah. those are the two they talk about. Missionwired nonprofit specific and they tout that they have a digital co-op, which means they have an email co-op. So, if you're a member of the co-op, you can go get additional email members. We'll be f** dead. why? Mhm.
Mark Donatelli: This is what we did I on the board at God was the name of that company in Atlanta. they had an commerce platform and we did a thing called audience expander.
01:05:00
Mark Donatelli: 
Mark Donatelli: So basically they would take non-competitive clients and allow them in the same geography to cross target and…
Mark Donatelli: make money and blah blah blah. So yeah, that makes sense.
Tom Hutchison: And so Wland is big.
Tom Hutchison: I mean, they do co-ops for everything. I mean, we're not even thinking about competing with land. so I think the opportunity is to be an omni channel co-op…
Mark Donatelli: 
Tom Hutchison: where you can do direct mail or email, telemarketing if it still happens.
Mark Donatelli: I got a guy.
Tom Hutchison: it's just there's got to be some differentiator and I don't think omni channel is not even a very interesting differentiator I think there's got to be some level of Yeah.
Mark Donatelli: This is the all-in-one that I was saying this is the all-in-one. This is the turnkey. hey, You're trying to raise half million dollars to build a new church if you want to go out and plant a church, you want to do this, you want to do that, what you're trying to raise money for this that cause, whatever. There's a turnkey solution for you and you just tick the boxes. I want direct mail. I want email. I want
Tom Hutchison: And the way it would work today is you would start with people that have donated before and…
Mark Donatelli: Yep.
Tom Hutchison: then you would go rent lists and then after merge purge if you have a shortfall then you would go to the co-op and do At no point do you start with and the co-op output becomes the last thing in your the least priority. And so there's not a scenario in which you start with a co-op and define what kind of a population you want. that's not the way they think about it.
Mark Donatelli: 
Mark Donatelli: the customer like the mailer…
Tom Hutchison: Still waiting for…
Mark Donatelli: who's the…
Tom Hutchison: if I had…
Mark Donatelli: who are all the mailers.
Tom Hutchison: if I had documentation, I would tell you. It's a Yeah,…
Mark Donatelli: Interesting. Yeah. Sounds like a hot mess. but the good news is Yep.
Tom Hutchison: it's the mess of a small company that has turned into a big company without noticing it. Yeah.
Mark Donatelli: And you know what? Databases and JavaScript and prototyping these are very inexpensive. We're not talking about the old days where you had to go get, six U's of rack space somewhere and a bunch of you had to really invest to spin something up. this shouldn't be hard to prototype these ideas. as long as the prototypes don't turn into the solution. Companies this size that happens sometimes.
Mark Donatelli: 
Mark Donatelli: All let's see what else we got on this list here.
Mark Donatelli: Tomorrow,…
Tom Hutchison: I need to run take care of something.
Tom Hutchison: Let's schedule another hour. I'm in on Tuesday and Wednesday. yeah.
Mark Donatelli: Sam, tomorrow, Wednesday.
Tom Hutchison: I want to walk you through two things. I want you to understand Perry and specifically I want you to think about from a data perspective. And remember, I'm trying to get the easy reputation builders, how we can position some of the things that you do in the context of Perry. So when I go pitch this to the rest of the company, they get it. And then two, that'll take about a half an hour for me to go through that flow. Nothing surprising there.
Tom Hutchison: And then I want to take a few minutes to walk through the wireframes that I've done and see if you're comfortable doing a prototype around that. and…
Mark Donatelli: 
Tom Hutchison: I am literally free all day. So there's a convenient time for you to pick it.
Mark Donatelli: I'm going to get right there in a second.
Mark Donatelli: Let me see something here. So, tomorrow is 11:26. Let me go to my calendar. Tomorrow, Gabe has practiced. So, let's not do the mobile thing in the middle again tomorrow. it did work. Let's go Is that right 12:30 Eastern.
01:10:00
Tom Hutchison: That's why
Mark Donatelli: All So, I'll send you another hour there and then we'll keep going.
Mark Donatelli: 
Mark Donatelli: This is good. I think there'll be stuff to do here, There's all kinds of work that you guys can need help with. I think that Matt's interesting guy. I met with Matt you've obviously talked to Matt probably more than I have obviously. I hadn't talked to Matt in a really really long time when I talked to him when you were going through the process.
Tom Hutchison: 
Mark Donatelli: And he's pretty straightforward guy. overall, I think he internalizes a lot of stuff, too, though. he says I think there's still stuff inside we got to pull out a little bit.
Tom Hutchison: Yeah. Yeah.
Mark Donatelli: He plays close to the vest.
Mark Donatelli: I guess he's direct, but he still keeps things kind of close to the vest. yeah.
Tom Hutchison: I mean and I think it's probably appropriate because he's having conversations about new acquisitions and stuff that we don't need to be having part in that because we're not affecting the decision and I don't know how much he is I mean I don't know how much any new acquisitions and…
Tom Hutchison: strategy changes are being driven by Behringer and how much of it's being driven by him.
Mark Donatelli: That's again a lot of times when they acquire companies,…
Mark Donatelli: depending on who's running the process, there's some investment thesis and we don't know the investment thesis right now.
Mark Donatelli: So the investment thesis sometimes the question is okay veridata is the center piece of the investment thesis. We're going to acquire capabilities that make verid and attach them and bolt them on and tuck them in to verata or veridata becomes a tuckin to something else.  I'm guessing it's the former there is a process when you go to change your names like there's kind of some stages you have to kind of go through.
Mark Donatelli: 
Mark Donatelli: And so yeah, I do think that ultimately, yeah, there's plenty of stuff to talk about. So, I just sent you that all right, good. So, we'll talk tomorrow then.
Tom Hutchison: Yeah, I just accepted it.
Tom Hutchison: All right, sounds like a plan.
Mark Donatelli: All right. Bye.
Tom Hutchison: See you.
Meeting ended after 01:13:35 👋
This editable transcript was computer generated and might contain errors. People can also change the text after it was created.


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