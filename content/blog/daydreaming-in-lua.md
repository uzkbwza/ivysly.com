Title: daydreaming with lua 
Slug: daydreaming-with-lua
Date: 2025-02-04
Status: published
Comments: 3lhfwi5bkjc2f

i think many programmers are conquerors. they want to bend reality to their will. to this end, making a software is an intense power fantasy, one where the programmer is given a problem and full control over a system to solve that problem, leveraging the unimaginable algorithmic power of the machine to obliterate tasks that would have taken human computers lifetimes of effort. 

in some capacity this is true also for creatives and really all people—there is an essential equivalence between making art and the process of daydreaming (the latter of which being a universal human experience) as commonly a form of wish-fulfillment. to develop a video game, i entertain both the power fantasy of programming and the wish-fulfillment of creative writing in a single process, to the immense satisfaction of my ego, and video games themselves achieve the highest potential for wish-fulfillment of any artistic medium.

at the beginning of 2024 i made a resolution to ditch Godot. I had used it for 6 years or so, and for much of that time i held so much optimism for it and its future. but years of big and little issues wore me down, and finally i decided it was time to move on. i was done with doing things the Godot Way.

instead i was going to build my own engine in FNA, a fork of XNA similar to Monogame, which uses the C# programming language. i really did try to do this, and i spent several months on the foundation for a 2d engine, but what i found is that C# and FNA became a sort of creative prison for me.

you see the problem is that i can't honestly describe myself as a *software developer* but instead as an intuitive *game artist*, who prefers freedom of expression without regard to the convention or maintenance needed of business software. what i need is rapid iteration, to unconsciously feel the impacts of tiny tweaks to the sensations of a game, not theorizing and calculating large swaths of changes all at once and waiting for the program to be "correct" before continuing.

C# is not made for artists, it is made for businesses. this is true for the majority of general-purpose programming languages. C# is bureaucratic and cold, tough but fair. it's not supposed to be a fun language because it is supposed to be a tool. it is the reflection of its creators who belong to a culture i reject as inhumane, thus its philosophy. so i have concluded that FNA just doesn't meet the needs of the sole *game artist* and could, worse, be actively harmful to artists who don't know any better. programming languages are not just one-way communication, they necessarily communicate to you how you ought to think about data and procedures, and in the case of the game artist this means your creative output.

the fact is, i wanted to try [LÖVE](https://love2d.org/) long before i was ever interested in FNA. but something scared me about Lua, the simple, dynamic, interpreted programming language used by LÖVE. to me its simplicity hid intimidating depth. i had used it once before but i never really took the time to understand it. metatables, weird keywords, global magic methods—this was all very alien, 1-indexed arrays the least of my concerns. but i knew, deeply, even before my doomed tryst with C#, LÖVE was what was missing in my heart. 

i have learned since i started using it that Lua is more than just pleasant to write. i should have been tipped off by the name and brand of the LÖVE framework: soft colors, rounded edges, a sort of pneumatic, inviting atmosphere to its website, which playfully warns that its community *"sometimes gets too friendly"*. all the clues are there. even the community-made libraries follow this theme, often explicitly; you will quickly find packages with names like *makelove*, *love bone*, *quickie*, *moan*, *hump*, and yes, *hardon collider*. this kind of thing might throw some people off, but after writing [my second Lua-powered game](https://ivysly.com/games/famulus.html), i have to say:

**i understand.**

Lua is a deeply erotic programming language. is this absurd to say? it is inviting and warm. there are no rules with Lua. it is not your boss but an equal and a companion. Lua says, "do what you want with me". it is surprising but fluid. debugging is more feeling than rigor. even the name is feminine and flirtatious. it is everything that C# is not. Lua i come home to.

sex is sort of like plugging in. despite having little in the way of modern package management, Lua allows the programmer to easily incorporate external library code unaltered, even with vast differences in structure, because Lua is highly polymorphic in both a mathematical and biological sense—that is, one API might be completely unrecognizable to the other, but you can still plug in. you could call that chemistry.

i must recognize that the source of my daydream is the subconscious. it is impossible to ignore that my desire to make art is deeply entangled in the immediate, libidinal drive of the id, and barely held enough together by my ego to result in coherent output. is it absurd to model and encourage this with my tools? Lua is as satisfying in this way as you can get in the form of a programming language (see also Lisp) because what it allows you to do maps directly to the innermost desires of the human psyche. Lua was made for pleasure and play. while this may not be a good fit for the anti-human culture of business software, i think the benefit to creatives is by now self-evident.

game artists are in a weird place where expression is steeped in procedure. art techniques are often formulaic, but the foundation of the art of programming is formula. this is where we make little prisons for ourselves. i would think the goal of the game artist is to instead build a bedroom.