"""Demo pool of foreign (mostly English) news items used to simulate a free News API feed."""

DEMO_NEWS = [
    {
        "source_title": "European Central Bank cuts interest rates by 25 basis points to 2.75%",
        "source_content": "The European Central Bank on Thursday lowered its key deposit rate by 25 basis points to 2.75%, the fifth cut since June 2024. ECB President Christine Lagarde said in Frankfurt that inflation across the 20-nation euro zone had eased to 2.4% in December, moving closer to the bank's 2% target. Lagarde noted that economic growth in the region remained weak, with Germany contracting by 0.2% in the fourth quarter. Analysts at Goldman Sachs expect two more rate reductions before July 2025.",
        "category": "व्यापार",
        "source_name": "Reuters",
    },
    {
        "source_title": "NASA's Europa Clipper spacecraft completes Mars flyby on its way to Jupiter",
        "source_content": "NASA confirmed on March 1 that its Europa Clipper spacecraft successfully completed a gravity-assist flyby of Mars, passing just 884 kilometers above the planet's surface. Launched from Cape Canaveral in October 2024, the $5.2 billion mission will travel 2.9 billion kilometers to reach Jupiter's icy moon Europa in April 2030. Project scientist Robert Pappalardo said the spacecraft will make nearly 50 close passes of Europa to determine whether the moon's subsurface ocean could support life.",
        "category": "तकनीक",
        "source_name": "Associated Press",
    },
    {
        "source_title": "Real Madrid defeats Manchester City 3-1 in Champions League playoff",
        "source_content": "Real Madrid beat Manchester City 3-1 at the Santiago Bernabeu on Wednesday night in the first leg of their Champions League playoff. Kylian Mbappe scored twice in the 60th and 78th minutes, while Erling Haaland pulled one back for City in the 84th minute. The result gives the 15-time European champions a strong advantage ahead of the second leg in Manchester next week. Coach Carlo Ancelotti praised his team's resilience after going a goal down early.",
        "category": "खेल",
        "source_name": "BBC Sport",
    },
    {
        "source_title": "Apple unveils new AI features and a foldable iPhone prototype at spring event",
        "source_content": "Apple on Tuesday previewed a range of artificial intelligence features for its devices and showed a foldable iPhone prototype for the first time at its headquarters in Cupertino, California. CEO Tim Cook said the foldable device, expected in 2026, would feature a 7.8-inch inner display. The company also announced that Apple Intelligence would support 12 new languages, including Hindi, later this year. Shares of Apple rose 3.4% following the announcement.",
        "category": "तकनीक",
        "source_name": "The Verge",
    },
    {
        "source_title": "United Nations warns global temperatures could rise 2.7 degrees by 2100",
        "source_content": "A new United Nations report released in Geneva on Monday warned that global average temperatures are on track to rise by 2.7 degrees Celsius above pre-industrial levels by the year 2100 unless countries dramatically cut emissions. UN Secretary-General Antonio Guterres called the findings a 'code red for humanity'. The report noted that 2024 was the hottest year on record, with global temperatures already 1.5 degrees above the 1850-1900 average.",
        "category": "दुनिया",
        "source_name": "The Guardian",
    },
    {
        "source_title": "Japan's economy grows 1.2% in fourth quarter, beating forecasts",
        "source_content": "Japan's economy expanded at an annualized rate of 1.2% in the October-December quarter, government data showed on Friday, exceeding economists' expectations of 1.0%. The growth was driven by strong exports and a rebound in consumer spending in Tokyo and Osaka. Finance Minister Katsunobu Kato said the Bank of Japan would carefully consider the data before its next policy meeting in March. The yen strengthened to 148 against the US dollar following the release.",
        "category": "व्यापार",
        "source_name": "Bloomberg",
    },
    {
        "source_title": "Hollywood film 'Silent Horizon' wins top prize at Berlin Film Festival",
        "source_content": "The American drama 'Silent Horizon', directed by Greta Larson, won the Golden Bear for best film at the 75th Berlin International Film Festival on Saturday. The film, which explores a family's struggle during a drought in rural Kansas, beat 18 other contenders. Lead actress Maya Chen won the Silver Bear for best performance. Festival director Tricia Tuttle said the jury was moved by the film's 'quiet power'. The festival attracted over 300,000 visitors this year.",
        "category": "मनोरंजन",
        "source_name": "Variety",
    },
    {
        "source_title": "Scientists in Australia develop battery that charges electric cars in 6 minutes",
        "source_content": "Researchers at the University of Sydney announced on January 20 that they have developed a new lithium-metal battery capable of charging an electric vehicle to 80% in just 6 minutes. Lead researcher Dr. Emily Watson said the battery uses a novel solid electrolyte that prevents overheating. The team, funded by a 40 million Australian dollar grant, expects the technology to reach commercial markets by 2028. The breakthrough could address one of the biggest hurdles to electric vehicle adoption.",
        "category": "तकनीक",
        "source_name": "ABC News",
    },
    {
        "source_title": "France and Germany sign new defence cooperation treaty in Paris",
        "source_content": "France and Germany signed a landmark defence cooperation treaty in Paris on Thursday, pledging to jointly develop a next-generation fighter jet by 2040. French President Emmanuel Macron and German Chancellor Friedrich Merz said the agreement would strengthen European security amid growing global tensions. The treaty includes a combined defence investment of 100 billion euros over the next 15 years. Both leaders emphasised the importance of European strategic autonomy.",
        "category": "दुनिया",
        "source_name": "Deutsche Welle",
    },
    {
        "source_title": "World Health Organization declares end to mpox global health emergency",
        "source_content": "The World Health Organization on Tuesday declared an end to the global health emergency for mpox, more than a year after it was first announced. WHO Director-General Dr. Tedros Adhanom Ghebreyesus said in Geneva that reported cases had fallen by 78% over the past six months. He credited coordinated vaccination campaigns across 40 countries. However, he cautioned that continued surveillance was necessary, particularly in parts of central Africa where the virus remains active.",
        "category": "दुनिया",
        "source_name": "CNN",
    },
    {
        "source_title": "Tesla recalls 375,000 vehicles over power steering software issue",
        "source_content": "Tesla is recalling approximately 375,000 vehicles in the United States due to a software fault that could affect power steering assistance, the National Highway Traffic Safety Administration said on February 10. The recall covers certain Model 3 and Model Y vehicles built between 2023 and 2025. Tesla said the issue would be fixed through a free over-the-air software update and that no injuries had been reported. Company shares dipped 1.8% in early trading.",
        "category": "व्यापार",
        "source_name": "Reuters",
    },
    {
        "source_title": "Argentina wins Copa America final against Brazil on penalties",
        "source_content": "Argentina defeated Brazil 4-2 on penalties after a 1-1 draw in the Copa America final held in Miami on Sunday night. Lionel Messi scored in the 22nd minute before Vinicius Junior equalised for Brazil in the 67th minute. Goalkeeper Emiliano Martinez saved two penalties in the shootout to secure the title for Argentina. It was Argentina's 16th Copa America trophy. The match was watched by a record crowd of 65,000 spectators at Hard Rock Stadium.",
        "category": "खेल",
        "source_name": "ESPN",
    },
]

CATEGORIES = ["दुनिया", "व्यापार", "तकनीक", "खेल", "मनोरंजन", "राजनीति"]

# Pre-written published seed articles so the public site is populated instantly.
SEED_ARTICLES = [
    {
        "source_title": "India's economy grows 7.2% in latest quarter, fastest among major economies",
        "source_name": "Financial Times",
        "category": "व्यापार",
        "rewritten_headline": "भारत बना दुनिया की सबसे तेज़ अर्थव्यवस्था, विकास दर पहुँची 7.2%!",
        "rewritten_article": "भारत की अर्थव्यवस्था ने एक बार फिर पूरी दुनिया को चौंका दिया है। ताज़ा तिमाही में देश की विकास दर 7.2% दर्ज की गई, जो सभी बड़ी अर्थव्यवस्थाओं में सबसे तेज़ है। विशेषज्ञों के अनुसार यह उछाल मज़बूत घरेलू माँग और बढ़ते निवेश की वजह से आया है। रिपोर्ट में बताया गया कि विनिर्माण और सेवा क्षेत्र दोनों में शानदार प्रदर्शन देखने को मिला। अर्थशास्त्रियों का मानना है कि आने वाले महीनों में यह रफ़्तार बनी रह सकती है।",
        "facts": [
            {"type": "आँकड़ा", "value": "7.2%"},
            {"type": "स्थान", "value": "India"},
            {"type": "स्रोत", "value": "Financial Times"},
        ],
        "image_prompt": "modern indian financial district skyline with rising graph, editorial news photo",
        "image_url": "https://images.pexels.com/photos/33305052/pexels-photo-33305052.jpeg?auto=compress&cs=tinysrgb&dpr=2&h=650&w=940",
    },
    {
        "source_title": "SpaceX successfully launches 60 satellites into orbit from Florida",
        "source_name": "Space.com",
        "category": "तकनीक",
        "rewritten_headline": "अंतरिक्ष में नया इतिहास: एक ही उड़ान में भेजे गए 60 सैटेलाइट!",
        "rewritten_article": "अंतरिक्ष तकनीक की दुनिया में एक और बड़ी छलांग लगी है। फ्लोरिडा से एक ही रॉकेट के ज़रिए 60 सैटेलाइट सफलतापूर्वक कक्षा में स्थापित किए गए। इस मिशन को लेकर वैज्ञानिकों में भारी उत्साह देखा गया। बताया जा रहा है कि इन सैटेलाइट से दुनिया भर में इंटरनेट कनेक्टिविटी और मज़बूत होगी। रॉकेट का पहला चरण सुरक्षित रूप से वापस धरती पर लौट आया, जिससे लागत में भारी कमी आने की उम्मीद है।",
        "facts": [
            {"type": "आँकड़ा", "value": "60 satellites"},
            {"type": "स्थान", "value": "Florida"},
            {"type": "स्रोत", "value": "Space.com"},
        ],
        "image_prompt": "rocket launching into blue sky with satellites, dramatic news photography",
        "image_url": "https://images.unsplash.com/photo-1784267978400-167fe8db5d95?crop=entropy&cs=srgb&fm=jpg&ixid=M3w4NjAzNDR8MHwxfHNlYXJjaHwxfHxicmVha2luZyUyMG5ld3MlMjBqb3VybmFsaXN0JTIwc3R1ZGlvJTIwY2FtZXJhfGVufDB8fHx8MTc4OTcwMzYzNHww&ixlib=rb-4.1.0&q=85",
    },
    {
        "source_title": "France wins FIFA friendly against Spain 2-0 in Paris",
        "source_name": "BBC Sport",
        "category": "खेल",
        "rewritten_headline": "पेरिस में फ्रांस का दबदबा, स्पेन को 2-0 से रौंदा!",
        "rewritten_article": "फुटबॉल प्रेमियों के लिए पेरिस की रात यादगार बन गई, जब फ्रांस ने स्पेन को एक रोमांचक मुक़ाबले में 2-0 से हरा दिया। दोनों टीमों के बीच शुरू से ही कड़ी टक्कर देखने को मिली, लेकिन फ्रांस की आक्रामक रणनीति आख़िर में भारी पड़ी। स्टेडियम में मौजूद हज़ारों दर्शकों ने अपनी टीम का जमकर उत्साहवर्धन किया। इस जीत के बाद फ्रांसीसी खेमे में जश्न का माहौल है।",
        "facts": [
            {"type": "स्कोर", "value": "2-0"},
            {"type": "स्थान", "value": "Paris"},
            {"type": "स्रोत", "value": "BBC Sport"},
        ],
        "image_prompt": "football stadium at night with players celebrating, editorial sports photo",
        "image_url": "https://images.pexels.com/photos/10464798/pexels-photo-10464798.jpeg?auto=compress&cs=tinysrgb&dpr=2&h=650&w=940",
    },
]
