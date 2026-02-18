
Publications
Themes
Event
Collaboration
research@kalshi.com

Election Accuracy
Slowly, Then All At Once: What Mamdani's Victory Tells Us About Information Aggregation
The Complete Story: Primary Success and General Election Concerns
Mamdani Primary Odds
May 28: First Signal
Jun 9: POLITICO
Jun 11: PPP Poll
Jun 16: NYT Anti-Endorsement
Jun 23: Early Vote
Jun 24: Victory
0.0
0.2
0.4
0.6
0.8
1.0
Mamdani Primary Probability
The Electability ParadoxDots mark key eventsPrimary Success → General Concern21-point discount (90% → 69%)Full recovery by Election Day
Democratic General Election Odds
Jun 16: Relief
Jun 23: Concern
Jun 24: Discount
Jul 29: Recovery
Nov 4: Victory
Electability Discount
0.65
0.70
0.75
0.80
0.85
0.90
0.95
1.00
Democratic General Probability
Nov 2024
Dec 2024
Jan 2025
Feb 2025
Mar 2025
Apr 2025
May 2025
Jun 2025
Jul 2025
Aug 2025
Sep 2025
Oct 2025
Nov 2025
Date (November 2024 - November 2025)
NB: The General Election market below runs on the assumption of the candidate leading the Democratic Primary prior to the declaration of the winner of said Primary election.

Abstract
This paper examines the trajectory of Zohran Mamdani's candidacy for the 2025 New York City Mayoral Election through the lens of prediction market data spanning November 2024 through November 2025. By analyzing minute-by-minute price movements across two distinct but related markets - the Democratic primary nomination market and the general election party victory market - we identify critical inflection points, assess market perceptions of electoral viability, and construct a data-driven narrative of an insurgent candidacy that defied initial expectations. Elections are noisy, with constantly-shifting dynamics and a wide array of events altering potential perceptions of their outcome. In this study, we find a clear information hierarchy that establishes the relative credibility and significance of data from distinct sources, pulling back the curtain on the mechanisms underlying prediction market information aggregation and public perception creation.

Published: January 2025
Updated: January 2025
Read time: 16 min
prediction markets
politics
electability
polling vs behavior
market microstructure
Introduction
Prediction markets have emerged as valuable instruments for understanding political dynamics, often demonstrating superior forecasting accuracy compared to traditional polling methods. These markets aggregate dispersed information through the creation of financial incentives that create price signals to reflect collective assessments of political probabilities.

On November 9, 2024, prediction markets priced Zohran Mamdani's probability of winning the NYC Democratic mayoral nomination at 7%. On June 24, 2025, at 9:03PM, those markets surged to 99% in a single minute. Between these two points lies a detailed record of how markets process political information in real time.

This study contributes to the literature on prediction markets and political forecasting in three ways. First, we employ minute-level data to examine market reactions with unprecedented temporal granularity, allowing us to isolate specific information shocks and their immediate effects. Second, we analyze two related but distinct markets simultaneously - the primary nomination market and the general election market - revealing how traders assess different dimensions of electoral viability. Third, we identify a clear information hierarchy in which behavioral data (actual voting patterns) commanded substantially greater market credibility than opinion polling, media endorsements, or elite political support. We additionally find evidence of sophisticated information parsing - with markets responding aggressively to undercurrents of Mamdani momentum even where absolute polling numbers continued to show a large margin of victory for Cuomo.

Methodology
Data
This analysis employs two comprehensive prediction market datasets from Kalshi, a CFTC-regulated prediction market exchange. The datasets track:

Primary Market: Zohran Mamdani's probability of winning the Democratic nomination (337,096 minute-level observations, November 9, 2024 – July 1, 2025)
General Election Market: Democratic Party probability of winning the mayoral general election (521,648 minute-level observations, November 9, 2024 – November 6, 2025)
Both datasets record the median transaction price within each one-minute interval, providing high-frequency data on market sentiment evolution.

Data Processing
To construct complete time series from sporadic trading activity, we employed a forward-fill methodology. This approach carries the last observed median price forward through periods of zero trading volume, ensuring continuous price series suitable for event study analysis. This method is standard in financial market microstructure research when examining markets with intermittent trading. Significant movements were classified as ≥5¢ threshold over the course of a day, with additional internal sensitivity testing for movement of ≥3¢ conducted across the same period. Finally, systematic event research was undertaken to correlate price changes (and their respective windows) to news coverage, polling releases, and campaign developments.

Mamdani's Victory Arc
Phase 1: Slowly
For six months, markets remained largely indifferent to Mamdani's campaign. Prices oscillated between 1-9%, with minimal trading volume (median 0 trades per day), and volatility appeared to capture noise rather than information.

During this period, the Mamdani campaign was building critical infrastructure that couldn't be immediately appreciated: distributed social media operations, volunteer networks, and powerful voter contact programs. In this period, no single tweet went viral, no endorsement appeared, and no polling breakthrough emerged. To markets (and other election observers), this organization remained largely invisible.

Phase 2: The First Signal - May 28, 2025
On the evening of May 28th, markets experienced their first major move - a 10.5 cent price move with modest trading volume. On this day, Emerson College Polling reported that support for Mamdani had surged from 1% in February to 23% in May, cutting Cuomo's lead from 12 points to 9, NY1 published campaign coverage, and social media metrics showed momentum picking up steam.

Though polls still displayed a clear expectation of a Cuomo victory, the incremental improvement of Mamdani's position from a total outsider to a potential contender for second place created a real point of inflection in market pricing. Even in a market that only rewards participants who correctly identify the eventual winner, participants backing Mamdani saw promise driven by his ability to make progress on closing a gap on the near-guaranteed victor, Cuomo. Taking a step back, this market confidence is not simply a reflection of polling, but also of the truth that it reveals - that Mamdani's social media campaign and grassroots organization was beginning to work to meaningfully change the odds, and that his messaging was beginning to resonate.

Phase 3: The Polling Phase June 1 - 15, 2025
Two major market moves happened within this two-week period.

First, on June 9, markets surged +9¢ following the publication of polling in POLITICO showing a further narrowing of Cuomo’s margin to only 2 points. This substantial market movement was recorded within just 20 minutes of the story’s publication.For a similar reason to before, this polling, even though it still leaned toward a Mamdani loss, indicated that he was gaining ground and momentum, and that the power of his coordinated messaging campaign was flowing through. On this day also, the Mamdani campaign launched an effort to enroll New Yorkers who had been otherwise registered in other states. Though only apparent ex-post via analysis of the early voting and total voter registration figures, this push successfully mobilized tens of thousands of young people to turn out and vote.

Second, an additional +10¢ jump followed Public Policy Polling on June 11th showing Mamdani leading Cuomo 35% to 31% for the first time. This third-party validation pushed Mamdani up to ~40% on Kalshi, approaching a coin-flip for the nomination.

Phase 4: The Crisis
Upon market open on Monday the 16th of June, the campaign experienced its largest single-day decline to date: -11¢. On this day, the Editorial Board of the New York Times published a scathing anti-endorsement of Mamdani - not merely withholding support but actively recommending readers to vote elsewhere. Indeed, the Board went so far as to say "We do not believe that Mr. Mamdani deserves a spot on New Yorkers' ballots." The swift and severe market response to this statement, which was extended into a second day on June 17th, revealed an information hierarchy: the Times' institutional authority outweighed even the endorsement of Bernie Sanders the following day, in the immediate assessment of the markets. Unlike many other media articles published, this one, which was a large, bold, and unexpected move from a major New York-based masthead appeared to seriously resonate.

The Crisis: Traditional Media Gatekeeping vs. Progressive Support
NYT Anti-Endorsement
Published
Decline Continues Despite
Bernie Endorsement
0.200
0.250
0.300
0.350
0.400
Primary Probability
Jun 15 10PM
Jun 16 04AM
Jun 16 10AM
Jun 16 04PM
Jun 16 10PM
Jun 17 04AM
Jun 17 10AM
Jun 17 04PM
Jun 17 10PM
Time
8 AM: NYT Impact
Bernie Sanders Endorsement
NB: The NYT Editorial Board published their anti-endorsement at approximately 5AM ET. However, Kalshi markets opened to trading at 8AM ET as this was prior to the Exchange's move to 24/7 Trading.

As Mamdani's odds fell in the Democratic Primary, the market for Democratic victory in the General Mayoral Election exhibited an opposite movement - gaining 7¢. This negative correlation demonstrates the sophistication of market reasoning - traders believed Mamdani would be a weaker General Election candidate than alternatives (perhaps because of a fear of an unpalatable "socialist" agenda). In so moving, traders created an "electability discount".

The Electability Paradox: Primary Success vs. General Election Concern
Mamdani Primary Probability
NYT Anti-Endorsement
Early VotingData
9:03 PMVictory Called
0.2
0.4
0.6
0.8
1.0
Primary Probability
Democratic General Election Probability
Relief Rally
ElectabilityConcern
DiscountContinues
0.70
0.75
0.80
0.85
0.90
General Probability
Jun 15
Jun 16
Jun 17
Jun 18
Jun 19
Jun 20
Jun 21
Jun 22
Jun 23
Jun 24
Jun 25
Date (June 2025)
The Electability Paradox: Primary Success vs. General Election Concern (June 15-25, 2025)

Phase 5: All at Once
One week after the crisis outlined above, Monday the 23rd of June brought dramatic movement (+24¢) on massive volume (30x what had been seen previously). On this day, three pieces of information arrived:

The Gothamist (alongside other outlets and media channels) reported that Mamdani's previously invisible push for early voter mobilization had worked - with more than double the number of New Yorkers casting ballots in early voting compared to the election immediately prior, and with substantial representation of new and younger voters. The NYC Board of Elections reported that 47% of votes were cast by those under 44, and 30% by those under 30.
Weather forecasts predicted extreme heat on the day of the Primary, projected to disproportionately affect older voters (Cuomo's base).
Emerson polling moved to show Mamdani dominating Cuomo in the overall ranked-choice selection.
At this stage, opinion polling gave way to adjudications of real-life voting behavior, and markets responded aggressively to hard behavioral evidence validating months of organizing claims.

By the day of the Primary election, the writing was on the wall. By 9:03PM, just three minutes after polls closed, Kalshi traders had declared the race over for Mamdani at 99% probability, and Kalshi called the race - well ahead of all other media and polling organisations.

The Electability Paradox
Analysis of the dual-market system reveals a striking paradox: as Mamdani's primary probability increased, Democratic general election probability decreased. This negative correlation was particularly pronounced during the critical June 16-24 period:

June 16 (NYT crisis): Primary -11¢ on the day, General +7¢
June 23 (early voting): Primary +24¢, General -7¢
June 24 (primary day): Primary +43¢, General -7¢
The Critical Week: Negative Correlation Between Primary Success and General Confidence
0.2
0.3
0.4
0.5
0.6
0.7
0.8
0.9
1.0
Mamdani Primary Probability
0.70
0.75
0.80
0.85
0.90
0.95
Democratic General Election Probability
Jun 15
Jun 16
Jun 17
Jun 18
Jun 19
Jun 20
Jun 21
Jun 22
Jun 23
Jun 24
Jun 25
Jun 26
Date (June 2025)
Primary: Mamdani
General: Democrats
The Critical Week: Negative Correlation Between Primary Success and General Election Confidence

The cumulative "electability discount" reached 21 percentage points (90% → 69%) as Mamdani's nomination became certain. This suggests traders believed Mamdani would face greater general election challenges than the incumbent or moderate alternatives, likely due to concerns about:

"Socialist" policy positioning
Vote-splitting in a general election
Moderate voter flight to Republican alternatives
From a market perspective, this indicates the ability of traders to dynamically process and represent anticipated spillovers, providing additional calibration for campaign understanding of the magnitude of perceived fears about policy platforms. However, this discount proved temporary and ultimately unfounded. By late July, the general election market began recovering (July 29: +8¢), and by November 4, Democrats won the general election at 99% probability, validating that initial electability concerns were attenuated by successful messaging over the course of the campaign.

Discussion
This study contributes to prediction market theory in several ways. First, our findings strongly support the efficient market hypothesis in political contexts when high-quality information is available. The rapid incorporation of polling data and especially behavioral voting data demonstrates that markets efficiently price political information when it arrives.

The six-month "invisible period" during which substantial organizational infrastructure was built without immediate market recognition reflects efficient pricing of available information rather than any market deficiency. Markets accurately priced the observable signals - early polling showed Mamdani at 1-3%, media coverage was minimal, and fundraising lagged competitors. When new information arrived demonstrating the campaign's organizational success (behavioral voting data), markets adjusted immediately and decisively.

The Information Hierarchy
Our empirical finding of a clear information hierarchy:

behavioral data > polling > media > endorsements

has important implications for understanding what information markets trust. This hierarchy follows a logical pattern: markets assign greatest weight to information that most directly predicts the outcome of interest.

Information Hierarchy: What Moved Markets Most (Primary)
+10.5¢
+9.0¢
+10.0¢
-18.0¢
+24.0¢
+43.0¢
Emerson Polling
(May 28)
POLITICO Publication
(Jun 9)
PPP Poll: Mamdani Leads
(Jun 11)
NYT Anti-Endorsement
(Jun 16-17)
Early Voting Data
(Jun 23)
Final Voting Data
(Jun 24)
Information Type
Behavioral
Polling
Media
−20
−10
0
10
20
30
40
Market Impact (Cents)
Information Hierarchy: What Moved Markets Most (Primary Market Price Changes)

Behavioral data commands premium pricing because it represents revealed preferences - actual votes cast - rather than stated intentions. Polling data receives moderate weight because, while based on stated intentions, it aggregates information across samples with known statistical properties and secondarily acts as a signalling mechanism for underlying momentum. Indeed, per the polling data in Appendix Table 1., it was primarily the latter subtext, not the former apparent reality which continued to largely back Cuomo, which the market appeared to be strongly responsive to. Traditional media shows mixed effects. The NYT anti-endorsement's -18¢ impact reveals that institutional media still commands significant credibility, particularly for negative information. Its impact was larger, perhaps, because of its surprise - the anti-endorsement wasn't just a statement of opposition - it was a signal that even neutral outlets were concerned. Similarly sized impacts were not reported across any other comparable media outlet, underlining the unique position of mastheads like the New York Times. Finally, However, the minimal response to political endorsements suggests markets view symbolic support skeptically unless accompanied by mobilization resources, particularly when coming from candidates naturally assumed to be ideologically aligned with those they are endorsing. Political endorsements generate minimal market movement, suggesting traders view them as largely ceremonial rather than indicative of actual electoral impact.

The "Slowly, Then All At Once" Dynamic
The temporal pattern observed: six months of stability followed by rapid adjustment, demonstrates efficient market pricing of available information throughout the campaign cycle. This pattern suggests that insurgent campaigns operate on two parallel tracks:

Observable track: Media coverage, polling, endorsements (immediately and accurately priced by markets)

Latent track: Voter registration, volunteer organizing, turnout infrastructure (not observable until behavioral data emerges)

The Mamdani campaign's success stemmed from building the latent track while markets efficiently priced the observable track as a standalone and as indicative of the latent. When polling and behavioral data from early voting revealed the success of this organizing infrastructure, markets adjusted rapidly and appropriately, demonstrating responsive and efficient information processing.

The Electability Paradox: Sophisticated Uncertainty Pricing
Perhaps the most striking finding is the persistent negative correlation between primary and general election markets. As Mamdani's nomination became certain, the general election market priced in a 21¢ "electability discount" that proved entirely unfounded. This pattern raises interesting questions about how markets process uncertainty about unconventional candidates.

However, this temporary mispricing may reflect appropriate uncertainty pricing rather than market failure. Traders correctly identified that a Mamdani nomination represented a departure from typical Democratic candidate profiles, and the initial discount may have reflected genuine uncertainty about general election performance rather than systematic bias. The market's subsequent recovery as Mamdani demonstrated broader appeal validates that traders were updating appropriately as new information arrived.

Limitations
Several limitations warrant mention. First, prediction markets represent the views of a specific population of traders, who may not be representative of the broader electorate. However, the strong predictive accuracy of these markets at critical junctures (early voting, primary day) suggests traders processed information effectively despite potential sample selection, and are incentivised to align with their view of the true outcome rather than their independent beliefs.

Second, our event identification methodology, while systematic, relies on post-hoc attribution of price movements to specific events. Unobserved information may have contributed to some price changes, though the temporal proximity of movements to identifiable events (e.g., 20 minutes after POLITICO publication) increases confidence in causal attribution. Further avenues for study may examine the exact information aggregation mechanisms that lead to outsized confidence shown by the market and its participants relative to more muted advantages or results implied by polls.

Third, this is a single-case study of one mayoral primary. Generalization would require assessment of whether the information hierarchy pattern holds across different electoral contexts. That said, the theoretical mechanisms identified here (i.e., the superiority of behavioral data and the initial organizational invisibility of grassroots efforts that deliver results over time) may actually apply broadly to insurgent campaigns.

Practical Implications
For campaign strategists, our findings suggest several practical insights:

Prioritize behavioral indicators: Markets respond most strongly to voter registration drives, early voting mobilization, and other behavioral data. Campaigns should prioritize activities that generate measurable behavioral signals, as these provide the most credible evidence of campaign strength.
Anticipate sophisticated electability analysis: Anticipate sophisticated electability analysis: Markets will appropriately distinguish between primary strength and general election viability for unconventional candidates. This creates opportunities to demonstrate broader appeal through consistent messaging and coalition maintenance as the campaign progresses.
Monitor high-frequency signals - markets capture momentum: Real-time prediction market data provides valuable intelligence about how new information is being processed by sophisticated political observers, offering a more responsive feedback mechanism than traditional polling. Unlike traditional analysis methods, prediction market trading incorporates the subtle subtext of results that goes beyond headline numbers in real time.
Appendix: Polling Data
The following table summarizes publicly available polling data from the 2025 NYC Democratic mayoral primary race, ordered chronologically from most recent to earliest. This data was originally collated by the New York Times.

Pollster	Dates	Sponsor	First Round	Final Round
Margin	Cuomo	Mamdani	Margin	Cuomo	Mamdani
YouGov	June 17-23	Yale Polling	Cuomo +10	38%	28%	Cuomo +14	57%	43%
HarrisX	June 11-22	Fix the City Democratic sp.	Cuomo +19	38%	19%	Cuomo +24	52%	28%
Emerson College	June 18-20	Nexstar, PIX 11	Cuomo +3	36%	34%	Mamdani +4	48%	52%
Manhattan Institute	June 11-16	—	Cuomo +13	43%	30%	Cuomo +12	56%	44%
Center for Strategic	June 13-16	Don't Rank Evil	Cuomo +8	38%	30%	Cuomo +4	52%	48%
Marist College	June 9-12	—	Cuomo +12	43%	31%	Cuomo +10	55%	45%
Honan Strategy	June 5-9	Destination Tomorrow	Cuomo +17	42%	25%	Cuomo +12	56%	44%
Expedition Strategy	June 3-7	Fix the City Democratic sp.	Cuomo +12	42%	30%	Cuomo +12	56%	44%
Public Policy Polling	June 6-7	Justin Brannan Democratic sp.	Mamdani +4	31%	35%	N/A	—	—
Data for Progress	May 30 - June 4	New Yorkers for Democratic sp.	Cuomo +7	40%	33%	Cuomo +2	51%	49%
Emerson College	May 23-26	Nexstar	Cuomo +12	35%	23%	Cuomo +9	54%	46%
Workbench Strategy	May 14-18	Zohran Mamdani Democratic sp.	Cuomo +13	40%	27%	Cuomo +12	56%	44%
Honan Strategy	May 15-18	Jewish Voters Cuomo	Cuomo +21	47%	26%	Cuomo +22	61%	39%
SurveyUSA	May 14-17	—	Cuomo +32	43%	11%	N/A	—	—
Marist College	May 1-8	—	Cuomo +22	44%	22%	Cuomo +20	60%	40%
Table 1: Summary of publicly available polling data. Cuomo leads highlighted in blue; Mamdani leads highlighted in orange.

Conclusion
Prediction markets aggregate political information with remarkable efficiency. They respond within minutes to new data, distinguish sophisticatedly between related but distinct probabilities, and update rapidly as uncertainties resolve. In an era of grassroots organizing and distributed campaigns, understanding what information markets value most: actual behavior over stated preferences, provides crucial insight for practitioners and academics alike.

←
Back to Research
Kalshi Research

Signal-rich market science

research@kalshi.com →
Navigate

Publications
Themes
Event
Collaboration
Stay connected

kalshi.com
@kalshi
LinkedIn
@kalshiresearch
© 2026 Kalshi. All rights reserved.
26