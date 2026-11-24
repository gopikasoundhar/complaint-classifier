"""Generate data/complaints.csv (starter dataset).

Complaints are composed from hand-written issue descriptions plus varied openers,
locations, durations and closers, so length and wording differ. This is a STARTER
dataset: replace/extend it with real or self-written complaints for better results.

Usage: python scripts/generate_dataset.py
"""
import csv
import random
from pathlib import Path

random.seed(42)
PER_CATEGORY = 130

ISSUES = {
    "Water Supply": [
        "there is no water supply in our street", "the tap water is muddy and smells bad",
        "water pressure is very low in the overhead tank line", "the main water pipeline is leaking at the junction",
        "the drinking water tanker has not been delivered", "municipal water comes only once in three days",
        "the borewell has dried up and there is no alternative supply", "the water meter shows wrong readings and the bill is inflated",
        "contaminated tap water is making children sick", "the public tap at the corner is broken",
        "water supply timing was changed without any notice", "a burst pipe is wasting thousands of litres of drinking water",
        "there is no drinking water in the government school", "the water tank in our colony has not been cleaned",
        "the new water connection has been pending for months", "the water is yellow in colour when the supply starts",
        "the hand pump in the village is not working", "the water tanker takes too long to arrive",
        "tap water has a chlorine smell too strong to drink", "the valve of the water line is stuck so our lane gets nothing",
        "the water supply stopped after the pipeline repair", "residents are forced to buy water cans every day",
        "my house gets no tap water while the next street gets plenty", "the overhead tank never fills because of weak pumping",
    ],
    "Roads": [
        "a big pothole on the main road is causing accidents", "the road was dug up for cable laying and never repaired",
        "the speed breaker is too high and damages vehicles", "the tar road has completely worn out after the rains",
        "the footpath is broken and unsafe for senior citizens", "road markings and the zebra crossing have faded away",
        "the bridge approach road has deep cracks", "construction material left on the road is blocking traffic",
        "the road to our village is not paved at all", "the traffic signal at the junction is not working properly",
        "the divider on the highway is damaged", "loose gravel on the road makes two wheelers skid",
        "the new road work has been left half finished", "a manhole cover is missing in the middle of the road",
        "encroachment on the road has reduced its width", "there are no signboards near the school zone road",
        "the flyover surface is uneven and cracked", "the cement road is broken with exposed iron rods",
        "the street is too narrow and full of potholes", "vehicles are getting damaged because of the broken tarmac",
        "the road shoulder has collapsed near the curve", "there is no proper road connecting our layout to the highway",
        "the bus route road is so bad that vehicles take double the time", "road repair was done with poor material and broke within days",
    ],
    "Electricity": [
        "there are frequent power cuts in our area every evening", "the transformer near our house is sparking",
        "the electricity bill is much higher than my actual usage", "the streetlights on our lane are not working",
        "a live wire is hanging from the pole", "voltage fluctuation is damaging our appliances",
        "the new electricity meter installation is pending", "there is no power since last night after the storm",
        "the electric pole is leaning dangerously", "we had a power outage for more than twelve hours",
        "a bill was generated without taking the meter reading", "the street light keeps flickering all night",
        "transformer overload causes a blackout every night", "the power connection to our shop has not been restored",
        "electrical wires are touching tree branches near the park", "the substation staff do not answer complaint calls",
        "unscheduled load shedding is affecting students during exams", "the service wire to our house is damaged",
        "the high mast light at the junction is not working", "the agricultural pump set gets only two hours of power",
        "the electricity board charged a penalty though we paid on time", "the street lamp post is dark and unsafe for women at night",
        "sparks are coming from the electric meter box", "the power supply trips every time it rains",
    ],
    "Sanitation": [
        "garbage has not been collected from our street", "the drain is blocked and sewage is overflowing",
        "the overflowing dustbin near the market attracts stray dogs", "the public toilet is dirty and has no water",
        "stagnant water in the open drain is breeding mosquitoes", "the sewage line is leaking onto the road",
        "garbage is being burnt near the colony causing smoke", "the sweeper does not come to clean our lane",
        "the open drain next to the school is a health hazard", "a dead animal on the roadside has not been removed",
        "the septic tank cleaning vehicle is not available", "waste is being dumped in the empty plot behind our houses",
        "the foul smell from the garbage dump is unbearable", "there are no dustbins in our ward",
        "the community toilet is locked and unusable", "drainage water is entering our houses during rain",
        "fogging has not been done despite dengue cases", "plastic waste is clogging the canal",
        "the garbage truck skips our area on collection days", "waste from drain cleaning was left lying beside the road",
        "the underground drainage is choked and smells terrible", "rats and flies are everywhere because the garbage is never lifted",
        "the market area is filthy and nobody cleans it", "the sewage treatment plant releases dirty water into the lake",
    ],
    "Public Transport": [
        "the bus on route 23 is always late", "buses are overcrowded during morning hours",
        "the bus stop has no shelter and no seating", "the conductor behaved rudely and refused to return change",
        "there is no bus service to our village after 6 pm", "the bus fare was increased without notice",
        "buses skip the stop even when passengers are waiting", "the bus is in poor condition with broken seats and windows",
        "train services on this line are frequently delayed", "auto drivers refuse to use the meter",
        "the new bus route promised to the college was never started", "no bus timetable is displayed at the stand",
        "the driver was driving rashly and overspeeding", "the bus pass counter is closed and passes are not issued",
        "seats reserved for women in the bus are always occupied", "buses do not enter the bus stand and halt on the highway",
        "there is no accessible seating for disabled passengers in buses", "the metro station escalator is out of order",
        "shared autos overcharge during peak hours", "bus frequency has reduced and we wait for an hour",
        "the last bus of the night has been cancelled", "the town bus ran out of fuel midway and passengers were stranded",
        "ticket machines in the bus do not give receipts", "students are not allowed to board the bus with their concession pass",
    ],
    "Healthcare": [
        "there is no doctor available at the primary health centre", "the government hospital has no medicines in stock",
        "the waiting time at the outpatient department is very long", "the ambulance did not arrive on time",
        "the hospital ward is unclean and the beds have no sheets", "the nurse refused to attend to my mother",
        "the X-ray machine in the hospital is not working", "the hospital pharmacy asks us to buy medicines outside",
        "the vaccination camp was cancelled without information", "there is no female doctor at the community health centre",
        "the emergency ward has no staff at night", "the hospital charged money for a free treatment",
        "the blood bank has no stock for patients", "the health centre in our village is closed most days",
        "the doctor prescribed only costly private tests", "there are no oxygen cylinders in the district hospital",
        "patients are made to sleep on the floor due to lack of beds", "the health insurance card was rejected at the hospital",
        "the dispensary is open only for two hours", "the anganwadi has no immunization supplies for children",
        "the doctor did not examine the patient properly and rushed us out", "the hospital staff were rude to elderly patients",
        "there is no lab technician so blood tests are delayed for days", "the maternity ward has no proper facilities for new mothers",
    ],
}

# A few free-form, differently-worded complaints per category (adds variety beyond templates)
FREEFORM = {
    "Water Supply": [
        "I have been without tap water for four days and the corporation helpline keeps saying a team will come. Nobody has come and my elderly parents are struggling.",
        "Water is not coming", "Please fix our drinking water problem", "The pipe near the temple has been gushing water since Sunday and the whole lane is wet",
        "Our apartment gets dirty brown water every morning, please test the supply",
    ],
    "Roads": [
        "I fell off my scooter yesterday because of the huge pothole outside the post office. This road has been like this since the monsoon.",
        "Road is very bad", "Please repair the road in front of our house", "The tar was laid only a month ago and it is already coming off in chunks",
        "Heavy vehicles use our narrow road and it has cracked all along the edge",
    ],
    "Electricity": [
        "We have had no electricity since the early morning and when I called the office they said the lineman is on leave. Shops in the whole street are closed.",
        "Power cut again", "Please change the electric meter", "The bill for this month is triple the usual amount even though we were out of town",
        "A tree fell on the line during the storm and the wires are still on the ground",
    ],
    "Sanitation": [
        "The garbage in front of our apartment has been rotting for ten days and the smell is making everyone sick. Please send the cleaning vehicle.",
        "Drain is overflowing", "Please clean the street", "Our lane smells terrible because the gutter has not been cleaned after the rain",
        "Stray dogs are tearing open the garbage bags that nobody collects",
    ],
    "Public Transport": [
        "I travel to work by bus every day and for the last two weeks the 8 am bus has been cancelled without any announcement, so I reach the office late.",
        "Bus is late", "Please start a bus to our area", "The driver did not stop at the stop and I missed my interview",
        "Too many people stand in the bus because only one bus runs on this route in the morning",
    ],
    "Healthcare": [
        "My father waited five hours at the government hospital and was finally told the doctor had left for the day. He is a diabetic patient and needed urgent care.",
        "No doctor in the hospital", "Please send medicines to the health centre", "The nurse at the clinic was very careless while giving my son the injection",
        "The ambulance number kept ringing and no one picked up when my neighbour had chest pain",
    ],
}

OPENERS = ["", "", "", "Please look into this: ", "I want to complain that ", "Sir/Madam, ",
           "This is to bring to your notice that ", "Request urgent action as ", "Respected officer, ",
           "We are facing a serious problem, ", "Kindly note that ", "Complaint: "]
PLACES = ["", "", "", " in Ward 12", " near the bus stand", " in Lakshmi Nagar", " in our colony", " in Muthialpet",
          " near the government school", " in Ariyankuppam", " at Anna Salai", " near the temple", " in our village",
          " on 100 Feet Road", " in Villianur", " near the market", " in our apartment complex"]
DURATIONS = ["", "", "", " for the last three days", " since last week", " for over a month", " for almost two weeks",
             " since yesterday", " for several months", " for the past few days"]
CLOSERS = ["", "", "", ".", " Please take action immediately.", " Kindly resolve this at the earliest.",
           " This is causing a lot of trouble to residents.", " We have complained many times but nothing has happened.",
           " Senior citizens and children are suffering the most.", " Request the authorities to look into it."]


def compose(issue: str) -> str:
    text = random.choice(OPENERS) + issue + random.choice(PLACES) + random.choice(DURATIONS) + random.choice(CLOSERS)
    text = text[0].upper() + text[1:]
    style = random.random()
    if style < 0.2:      # casual: lowercase, no punctuation
        text = "".join(c for c in text.lower() if c.isalnum() or c.isspace())
    elif style < 0.25:   # shouting
        text = text.upper()
    return text.strip()


def main():
    rows = []
    for category, issues in ISSUES.items():
        seen = set(FREEFORM[category])
        texts = list(FREEFORM[category])
        # short variants: the bare issue
        for issue in issues:
            t = issue[0].upper() + issue[1:]
            seen.add(t)
            texts.append(t)
        while len(texts) < PER_CATEGORY:
            t = compose(random.choice(issues))
            if t.lower() not in {s.lower() for s in seen}:
                seen.add(t)
                texts.append(t)
        rows += [(t, category) for t in texts]
    random.shuffle(rows)
    out = Path(__file__).resolve().parent.parent / "data" / "complaints.csv"
    with open(out, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["text", "category"])
        w.writerows(rows)
    print(f"Wrote {len(rows)} rows to {out}")


if __name__ == "__main__":
    main()
