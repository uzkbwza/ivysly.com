Title: solo gamedev with lisp
Date: 2025-12-14
Slug: sologamedev-with-lisp
Comments: 3m7yveicck226

this last month or so i have been using the [Fennel programming language](https://fennel-lang.org/), a Lisp dialect that transpiles to Lua. if you want the quick pitch: it's a fast, imperative-oriented Lisp with macros that i think is perfectly suited to solo indie gamedev. i love it for all the reasons [i love Lua](https://ivysly.com/blog/daydreaming-with-lua.html) and more.

i had been interested in using a Lisp for some time—actually, had i the option, i would have probably picked a hypothetical LuaJIT With Macros first—but it always felt like there were hurdles and gotchas that prevented me from using it productively in game development. first is that the ecosystem is obviously pretty tiny for many Lisps. tooling, build systems and libraries can be a bit DIY, especially if you are not using Emacs (i might give it another go, now). Fennel circumvents much of this by just being Lua. [paredit](https://marketplace.visualstudio.com/items?itemName=JarodWright.strict-paredit-fennel) + [parinfer](https://marketplace.visualstudio.com/items?itemName=eduarddyckman.vscode-parinfer) with VS Code does the job of removing the parentheses pain well enough. this is the lesser issue. the bigger barrier is that Lisps are generally regarded as being on the functional side of programming languages, which, in the gamedev universe, means unknown, treacherous waters. games are highly stateful, highly imperative systems. it can be onerous trying to squeeze the slippery shape of a game into [the result of a pure function](https://prog21.dadgum.com/23.html). not to say that functional techniques have no place in gamedev, just that i find it difficult to apply them at the structural level. while some people are happy to take on such a challenge, i feel it is more practical for me to work in a perspective i'm familiar with. Fennel just so happens to feel exactly like Lua with a different syntax, because it is. i'm essentially doing the same things i was doing before, with a few trade-offs. this led me to a breakthrough: Lisp doesn't have to be anything. there are very few limits on what they *can* be. a Lisp has become in my mind solely defined as a direct representation of an AST made of [s-expressions](https://igor.io/2012/12/06/sexpr). you've probably seen s-expressions before. they're just hiding in JSONs and [XMLs](https://defmacro.org/ramblings/lisp.html). you can write a Lisp with all the features of another language. it doesn't even need to have a linked list data structure (Fennel's lists only exist at compile time—even then, you spend most of your time just interfacing with Lua tables, with lists themselves in fact just being tables with some metadata). any other preconceptions you have about Lisp, you can safely let them go. [Lisps don't even need to have parentheses](https://srfi.schemers.org/srfi-49/srfi-49.html).

Fennel is not really at all a pure-functional or declarative language. due to the severe restriction of being a zero-overhead Lua transpiler, the Fennel language doesn't even ship with any of its own functions. what it does have is access to all of Lua's built-in functions and table operations, many of which are good old imperative, stateful operations. you very well *could* turn Fennel into a pure, declarative language, or you could do something completely different. that's because Fennel (and Lisp) isn't really anything at all but a syntax. it doesn't have to be anything until you make it something, and you are given carte blanche to do so with macros.

with macros, a Lisp essentially becomes an extension of the programmer's mental model of the program. it's amazing how simple it is. you should probably exercise more prudence in teams, but as a solo developer, it's pretty amazing to be able to freely add my own natural-language constructs to the language with no runtime overhead. for example, one of the most common mathematical operations i tend to do in game dev is dividing things by two. `somevar / 2` shows up hundreds or thousands of times in my typical code bases. in Fennel (and most other Lisps), it's dead simple to introduce a macro `(half somevar)` that compiles to the same thing, both reducing symbol noise and increasing clarity of intent. there's no function call overhead, so the only reason not to use it is when semantically it wouldn't make sense. this i think is an incredible feature for idiosyncratic solo devs like me, because while you might make your code [unreadable for anyone but you](https://marktarver.com/bipolar.html), it can become highly readable *for you*, and even more so quickly writeable. again, a Lisp can be *anything*. this means it can be exactly what you want out of a programming language, with technically no concessions except that you might have to put in the work to get it there (there is a reason most DSLs written in Lisp tend to look a lot like Lisp).

Fennel and [LÖVE](https://love2d.org/) go very well together. i have found that plugging into my existing codebase was very easy. even getting an in-game REPL going only took a few minutes, and already i can sense the crazy amount of power it gives me to tweak things on the fly. and since it's just Lua, it might be one of the faster Lisps when JITted with a great incremental garbage collector, very well suited to gamedev. being a solo dev, for me, means writing stuff quickly without spending too much time on tedious bookkeeping and careful structuring one might need to do in a larger team. for the lone gamedev, i think a controlled amount of yolo-coding is how you get shit made. this is a huge strength of Lisp.

one funny problem with the switch from Lua is that now my engine uses three naming conventions; camelCase for the `love` namespace, snake_case for my own preferred identifier style in Lua, and now kebab-case for all the symbols in Lisp. things can get pretty hairy when writing code that interfaces with all of these. nothing i can't fix by rewriting my whole engine in Fennel of course.

another small pain point is the notation for arithmetic. it's just not as intuitive to read `a * b + c + d - e - f` in the prefix notated form `(+ (* a b) c (- d e f))`, but i suspect it could eventually end up being just about so, and i'm already developing adequate proficiency anyway. disregarding Lisp for this reason feels about as arbitrary and nitpicky as dismissing Lua for starting array indices at 1. you get used to it.

as of writing i have only one completed project in Fennel. i just released a [jam game](../games/fishbone.html) i made largely with Fennel, plugged in to my Lua LÖVE engine. i suspect my opinion will change in various ways as i continue to use it.

anyway with my main theses out of the way i am excited to just jabber more about the ridiculous utility of macros. the real pervert crap. it's often the case that you want to repeat the same complicated logic on multiple values across multiple lines, but introducing a lambda (in Lua, at least) may add an unacceptable performance overhead, and putting it somewhere else in the program restricts its utility as a closure. on the contrary, inline macros let you capture the context like a closure and duplicate logic without polluting your code with a bunch of repeated procedures (which could easily break should you forget to update all of them when you need to change it), with none of the overhead of creating and calling an actual function. as a very minimal example, imagine this naive code, in the input handling function for the player somewhere:

    :::fennel
    (if (input-held? "up")
      (move-player! 0 (* (- speed) delta)))
    (if (input-held? "down")
      (move-player! 0 (* speed delta)))
    (if (input-held? "left")
      (move-player! (* (- speed) delta) 0))
    (if (input-held? "right")
      (move-player! (* speed delta) 0))

in this example, it would be overkill to introduce a local function to simplify the logic, and is currently a lot of noise to repeat the logic for each direction. a macro can combine the best of both options while making the important logic much more clear. plus it keeps all relevant code in the same place without you needing to search for another function that exists somewhere else. it does all this with no runtime overhead, as the following snippet compiles to code roughly equivalent to the previous block:

    :::fennel
    (macro player-input-move! [...]
    `(do ,(unpack
      (fcollect [i 1 (select :# ...) 3]
        (let [(input dirx diry) (select i ...)]
          `(if (input-held? ,input)
              (move-player!
              (* ,dirx speed delta)
              (* ,diry speed delta))))))))

    (player-input-move!
      "up" 0 -1
      "down" 0 1
      "left" -1 0
      "right" 1 0)

this compiles to:

    :::fennel
    (do
      (if (input-held? "up")
        (move-player! (* 0 speed delta) (* -1 speed delta)))
      (if (input-held? "down")
        (move-player! (* 0 speed delta) (* 1 speed delta)))
      (if (input-held? "left")
        (move-player! (* -1 speed delta) (* 0 speed delta)))
      (if (input-held? "right")
        (move-player! (* 1 speed delta) (* 0 speed delta))))


the only meaningful difference being a few extra (cheap) multiplications, which could easily be refactored out as needed. i'd bet money that LuaJIT ignores multiplications by zero literal on hot loops anyway. when performance isn't a concern, it usually will be cleaner to simply write a function, of course, but game dev performance is often death by a thousand cuts, with lots and lots of little inefficiencies that pile up. macros in Fennel allow you to define behavior *anywhere* free of risk.

you can get a lot more complicated than this too. i wrote DSLs for defining object classes and state machines. the latter only took an afternoon. I'll leave you with what i am calling the [brohoof operator](https://bsky.app/profile/ivysly.com/post/3m7jtgmthek2c): a macro that divides two values in the opposite order they are passed:

    :::#fennel
    (macro \ [lhs rhs]
      `(/ ,rhs ,lhs))

    (\ 2 1)
    >> 0.5
