import random
from tickets.models import Ticket

SUBJECTS_BY_CATEGORY = {
    Ticket.Category.ASSESSMENT: [
        "Assessment submission issue",
        "Problem with coursework submission",
        "Unable to upload assignment",
        "Assessment deadline clarification",
        "Grade not visible on portal",
        "Issue accessing assessment instructions",
        "Problem with exam timetable",
        "Exam clash concern",
    ],
    Ticket.Category.WELFARE: [
        "Request for welfare support",
        "Personal circumstances affecting studies",
        "Looking for student support services",
        "Concern about wellbeing support",
        "Advice regarding personal difficulties",
    ],
    Ticket.Category.CAREERS: [
        "Careers advice appointment request",
        "Internship opportunity question",
        "CV review support",
        "Help finding placement opportunities",
        "Graduate job support request",
    ],
    Ticket.Category.FINANCIAL_ISSUES: [
        "Financial hardship support enquiry",
        "Unexpected tuition fee charge",
        "Student funding clarification",
        "Problem with bursary payment",
        "Financial advice request",
    ],
    Ticket.Category.UNI_PROCEDURES_REGULATIONS: [
        "Clarification on university regulations",
        "Question about academic procedures",
        "Policy clarification request",
        "Concern regarding university regulations",
    ],
    Ticket.Category.ADMINISTRATION: [
        "Administrative support request",
        "Student record update issue",
        "Portal information incorrect",
        "General administrative enquiry",
    ],
    Ticket.Category.APPEALS_COMPLAINTS_AND_MISCONDUCT: [
        "Advice on academic appeal process",
        "Concern regarding complaint procedure",
        "Seeking guidance on misconduct report",
        "Issue related to academic complaint",
    ],
    Ticket.Category.DIGNITY_AND_INCLUSION: [
        "Concern regarding inclusivity",
        "Reporting dignity and inclusion issue",
        "Advice on inclusivity support services",
    ],
    Ticket.Category.DISABILITY_SUPPORT: [
        "Disability support enquiry",
        "Reasonable adjustment request",
        "Support plan clarification",
        "Access arrangements for exams",
    ],
    Ticket.Category.DOCUMENT_AND_LETTER_REQUESTS: [
        "Request for official letter",
        "Need proof of enrolment",
        "Transcript request",
        "Student status letter required",
    ],
    Ticket.Category.FEES_FUNDING_AND_MONEY_ADVICE: [
        "Tuition fee clarification",
        "Student finance issue",
        "Funding eligibility question",
        "Advice regarding funding options",
    ],
    Ticket.Category.GRADUATION: [
        "Graduation ceremony information",
        "Graduation eligibility question",
        "Issue with graduation registration",
        "Graduation documentation request",
    ],
    Ticket.Category.HEALTH_AND_WELLBEING: [
        "Health support enquiry",
        "Wellbeing services question",
        "Mental health support request",
        "Accessing wellbeing services",
    ],
    Ticket.Category.HOUSING_AND_ACCOMMODATION_SUPPORT: [
        "Accommodation issue enquiry",
        "Advice regarding housing support",
        "Problem with university accommodation",
        "Housing support request",
    ],
    Ticket.Category.INDUSTRIAL_ACTION: [
        "Concern about teaching disruption",
        "Impact of industrial action on modules",
        "Lecture cancellations due to strikes",
    ],
    Ticket.Category.NEW_STUDENTS: [
        "New student onboarding question",
        "Information for new students",
        "Orientation information request",
    ],
    Ticket.Category.RETURNING_TO_STUDY: [
        "Advice about returning to study",
        "Re-enrolment process question",
        "Support for returning students",
    ],
    Ticket.Category.STUDENT_LIFE: [
        "Student society information",
        "Looking for student activities",
        "Advice on student engagement opportunities",
    ],
    Ticket.Category.VISAS_IMMIGRATION_AND_SUPPORT: [
        "Visa documentation question",
        "Student visa advice request",
        "Immigration compliance question",
    ],
    Ticket.Category.OTHER: [
        "General enquiry",
        "Request for information",
        "Need advice regarding university services",
    ],
}

FACULTY_BODY = {
    Ticket.Faculty.FOLSM: [
        "This issue is affecting my coursework within the Faculty of Life Sciences & Medicine.",
        "I am currently studying within FoLSM and this is impacting my academic progress.",
        "My programme within the Faculty of Life Sciences & Medicine requires clarification on this matter.",
        "This concern relates to my studies in the Faculty of Life Sciences & Medicine.",
        "The issue is affecting my work within my FoLSM programme.",
        "I rely on resources provided by FoLSM and this issue is preventing me from accessing them.",
    ],
    Ticket.Faculty.SSPP: [
        "As a student in the Faculty of Social Science & Public Policy, this issue is affecting my studies.",
        "My programme within SSPP requires access to this information or support.",
        "This issue relates to my studies within the Faculty of Social Science & Public Policy.",
        "I am currently studying within SSPP and would appreciate clarification on this matter.",
        "This concern is impacting my coursework within the Social Science faculty.",
        "I would appreciate assistance as this issue is affecting my SSPP programme.",
    ],
    Ticket.Faculty.NMPC: [
        "This concerns my programme within the Florence Nightingale Faculty of Nursing, Midwifery & Palliative Care.",
        "As a student within the Florence Nightingale Faculty, this issue is affecting my coursework.",
        "This matter relates to my studies within the Nursing, Midwifery & Palliative Care faculty.",
        "The issue is impacting my academic work within the Florence Nightingale Faculty.",
        "I am currently enrolled in NMPC and would appreciate assistance with this issue.",
        "This situation is affecting my coursework within the Nursing and Midwifery programme.",
    ],
    Ticket.Faculty.NMES: [
        "This is affecting my work within the Faculty of Natural, Mathematical & Engineering Sciences.",
        "I rely on resources provided by NMES for my academic work.",
        "This issue is impacting my coursework within the NMES faculty.",
        "My studies within Natural, Mathematical & Engineering Sciences are affected by this issue.",
        "This concern relates directly to my programme within the NMES faculty.",
        "I would appreciate support as this problem is affecting my NMES coursework.",
    ],
    Ticket.Faculty.AH: [
        "This issue is affecting my studies within the Faculty of Arts & Humanities.",
        "My coursework in A&H requires clarification on this matter.",
        "I am currently studying within the Arts & Humanities faculty and this issue is impacting my work.",
        "This concern relates to my programme within the Faculty of Arts & Humanities.",
        "I would appreciate guidance regarding this issue affecting my A&H coursework.",
        "The matter is impacting my academic work within the Arts & Humanities faculty.",
    ],
    Ticket.Faculty.KBS: [
        "This issue relates to my programme within King's Business School.",
        "My coursework within KBS is affected by this issue.",
        "As a student in King's Business School, I would appreciate clarification regarding this matter.",
        "This concern is impacting my studies within the KBS faculty.",
        "I rely on resources provided through King's Business School and currently cannot access them.",
        "This issue is affecting my academic progress within my KBS programme.",
    ],
    Ticket.Faculty.DOCS: [
        "This issue relates to my programme within the Faculty of Dentistry, Oral & Craniofacial Sciences.",
        "As a DOCS student, this matter is impacting my coursework.",
        "I am currently studying within the Faculty of Dentistry and would appreciate assistance.",
        "This concern relates to my academic work within the DOCS faculty.",
        "My studies within Dentistry, Oral & Craniofacial Sciences are affected by this issue.",
        "I would appreciate guidance regarding this issue affecting my DOCS programme.",
    ],
    Ticket.Faculty.DPSOL: [
        "This affects my studies within the Dickson Poon School of Law.",
        "As a law student within DPSoL, this issue is impacting my coursework.",
        "This concern relates to my academic work within the Dickson Poon School of Law.",
        "My law programme within DPSoL is affected by this issue.",
        "I would appreciate assistance regarding this matter affecting my studies within the law faculty.",
        "This issue is impacting my academic progress within the Dickson Poon School of Law.",
    ],
    Ticket.Faculty.IOPPN: [
        "This issue impacts my studies within the Institute of Psychiatry, Psychology & Neuroscience.",
        "As a student within IoPPN, this matter is affecting my academic work.",
        "My programme within the Institute of Psychiatry, Psychology & Neuroscience is affected by this issue.",
        "I would appreciate clarification regarding this matter impacting my IoPPN studies.",
        "This concern relates directly to my coursework within the IoPPN faculty.",
        "The issue is affecting my academic progress within the Institute of Psychiatry, Psychology & Neuroscience.",
    ],
}

STUDY_LEVEL_BODY = {
    Ticket.StudyLevel.UNDERGRADUATE: [
        "I am currently studying at undergraduate level.",
        "This is related to my undergraduate coursework.",
        "As an undergraduate student, this issue is affecting my studies.",
        "This concern is impacting my undergraduate programme.",
        "I am completing my undergraduate degree and would appreciate guidance on this matter.",
        "This issue is affecting my progress within my undergraduate course.",
        "As an undergraduate student, I rely on the university systems involved in this matter.",
        "This issue is preventing me from completing my undergraduate coursework effectively.",
    ],
    Ticket.StudyLevel.POSTGRADUATE_TAUGHT: [
        "I am currently enrolled in a postgraduate taught programme.",
        "This issue is affecting my postgraduate coursework.",
        "As a postgraduate taught student, this issue is impacting my studies.",
        "This matter relates to my postgraduate taught programme.",
        "I am completing a master's level programme and would appreciate guidance regarding this issue.",
        "This concern is affecting my postgraduate taught coursework and assessments.",
        "As a postgraduate taught student, this issue is impacting my academic progress.",
        "This problem is affecting my postgraduate taught programme requirements.",
    ],
    Ticket.StudyLevel.POSTGRADUATE_RESEARCH: [
        "I am a postgraduate research student and this impacts my research work.",
        "This issue is affecting my dissertation or research progress.",
        "As a postgraduate research student, this concern is impacting my academic work.",
        "This matter relates directly to my doctoral or research programme.",
        "I rely on university resources for my research and this issue is preventing progress.",
        "This issue is affecting my ongoing research project.",
        "As a research student, this matter is impacting my ability to continue my work.",
        "This concern relates to my thesis or dissertation research.",
    ],
    Ticket.StudyLevel.OTHER: [
        "My programme falls under a different study category and I would appreciate guidance.",
        "My course structure is slightly different from the standard study levels and I would appreciate clarification.",
        "This issue relates to my specific programme structure.",
        "I am studying under a different academic arrangement and would appreciate advice.",
        "My study level does not fall under the standard categories and I would like guidance.",
    ],
}

CATEGORY_BODY = {
    Ticket.Category.ASSESSMENT: [
        "When attempting to submit my assessment through the portal I encountered an error.",
        "I would appreciate clarification on the assessment requirements and submission process.",
        "The submission page appears to be unavailable or not accepting uploads.",
    ],
    Ticket.Category.WELFARE: [
        "I am currently experiencing circumstances that are affecting my ability to focus on my studies.",
        "I would like to know what welfare or pastoral support services are available.",
        "I would appreciate guidance regarding student wellbeing support.",
        "Some personal circumstances are affecting my ability to keep up with coursework.",
        "I am looking for advice about available welfare support options.",
        "I would like to discuss support available during a difficult personal situation.",
    ],
    Ticket.Category.CAREERS: [
        "I would like guidance regarding career planning and internship opportunities.",
        "I am interested in accessing career services to help with my job applications.",
    ],
    Ticket.Category.FINANCIAL_ISSUES: [
        "I have encountered financial difficulties that may affect my ability to continue my studies.",
        "I would appreciate advice regarding financial support options available to students.",
        "I am looking for guidance regarding financial hardship support.",
        "Unexpected costs have arisen and I would like advice on available financial support.",
        "I would appreciate information about emergency financial assistance.",
        "I am experiencing financial pressure and would like advice on possible support services.",
    ],
    Ticket.Category.UNI_PROCEDURES_REGULATIONS: [
        "I would appreciate clarification regarding the relevant university procedures and regulations.",
        "I am unsure how the university policy applies in my situation and would like some guidance.",
        "I have reviewed the available documentation but would like confirmation on the correct process.",
        "Could you clarify how university regulations apply to my situation?",
        "I would like advice on how to proceed under the relevant academic regulations.",
        "The university policy documentation seems unclear and I would appreciate clarification.",
    ],
    Ticket.Category.ADMINISTRATION: [
        "I believe there may be an issue with my student record or administrative information.",
        "I would appreciate assistance resolving this administrative matter.",
        "Could you please advise how this administrative issue can be resolved?",
        "My portal information may need to be updated and I would appreciate assistance.",
    ],
    Ticket.Category.APPEALS_COMPLAINTS_AND_MISCONDUCT: [
        "I would like guidance regarding the process for submitting an academic appeal or complaint.",
        "I believe there may have been an issue affecting my academic outcome and would like advice on the next steps.",
        "I would appreciate clarification on the procedures for addressing academic misconduct or complaints.",
    ],
    Ticket.Category.DIGNITY_AND_INCLUSION: [
        "I would like to raise a concern related to dignity and inclusion within the university environment.",
        "I would appreciate advice on how to address an inclusivity concern within my programme or department.",
        "I am seeking guidance on available support related to dignity and inclusion matters.",
        "I would like to understand the process for submitting a formal appeal.",
        "I believe there may have been an administrative error affecting my result.",
        "I would like advice regarding how to proceed with a complaint.",
    ],
    Ticket.Category.DISABILITY_SUPPORT: [
        "I would like information about reasonable adjustments available for students with disabilities.",
        "I would appreciate guidance on how to access disability support services.",
    ],
    Ticket.Category.DOCUMENT_AND_LETTER_REQUESTS: [
        "I require an official document confirming my student status.",
        "Could you advise how I can obtain an official letter or transcript?",
    ],
    Ticket.Category.FEES_FUNDING_AND_MONEY_ADVICE: [
        "I have questions regarding tuition fees and the available funding options.",
        "I would appreciate guidance regarding financial support or funding available to students.",
        "I am seeking advice about managing tuition fees and available financial assistance.",
        "I would like clarification regarding academic adjustments for my circumstances.",
        "I would appreciate information about available accessibility support services.",
    ],
    Ticket.Category.GRADUATION: [
        "I would like clarification regarding the graduation process and requirements.",
        "Could you confirm my eligibility for the upcoming graduation ceremony?",
    ],
    Ticket.Category.HEALTH_AND_WELLBEING: [
        "I would appreciate information about health and wellbeing services available to students.",
        "I am looking for support resources related to student wellbeing.",
    ],
    Ticket.Category.HOUSING_AND_ACCOMMODATION_SUPPORT: [
        "I am experiencing issues related to accommodation and would appreciate advice.",
        "I would like guidance regarding available housing support options.",
        "I would appreciate advice regarding accommodation concerns.",
        "I am currently facing difficulties with my accommodation arrangements.",
    ],
    Ticket.Category.INDUSTRIAL_ACTION: [
        "I would like clarification regarding how industrial action may affect my teaching and assessments.",
        "Some scheduled teaching sessions have been disrupted and I would like to understand how this will impact my studies.",
        "Could you advise how ongoing industrial action might affect coursework deadlines or learning resources?",
    ],
    Ticket.Category.NEW_STUDENTS: [
        "As a new student I would appreciate guidance on accessing key university services.",
        "I would like more information about getting started with my programme and university systems.",
        "Could you provide advice for new students navigating university resources and support services?",
        "I am a new student and would like guidance on how to access important systems.",
        "Could you advise where new students can find essential university information?",
    ],
    Ticket.Category.RETURNING_TO_STUDY: [
        "I am planning to return to my studies and would like guidance on the required process.",
        "I would appreciate advice regarding re-enrolment and returning to my programme.",
        "Could you clarify the steps involved in returning to study after a break?",
    ],
    Ticket.Category.STUDENT_LIFE: [
        "I would like information about student activities, societies, or engagement opportunities.",
        "Could you advise how I can get involved in student life and extracurricular activities?",
        "I am interested in learning more about the opportunities available to students outside of coursework.",
        "I would appreciate advice about social and extracurricular opportunities available to students.",
        "I would like to know more about events or activities organised for students.",
    ],
    Ticket.Category.VISAS_IMMIGRATION_AND_SUPPORT: [
        "I have questions regarding my visa status and compliance requirements.",
        "I would appreciate guidance on immigration-related support services.",
        "Could you advise how to access visa and immigration support services?",
        "I would appreciate advice regarding documentation required for visa compliance.",
    ],
    Ticket.Category.OTHER: [
        "I would appreciate assistance or direction regarding this enquiry.",
        "Please let me know if further information is required.",
        "I would appreciate guidance regarding this matter.",
        "Could you advise how I should proceed with this issue?",
        "I am seeking assistance regarding a general enquiry.",
        "I would appreciate any advice or direction on this matter.",
    ],
}

STANDALONE_STUDENT_COMMENTS_BY_CATEGORY = {
    Ticket.Category.ASSESSMENT: [
        "I'm having some trouble completing one of my assessments and wanted to check what I should do.",
        "I wanted to ask for clarification about an assessment requirement.",
        "I'm not sure if I've followed the correct steps for submitting my assessment.",
        "I'm a bit confused about the expectations for one of my coursework submissions.",
        "Could someone help clarify something related to an upcoming assessment?",
    ],
    Ticket.Category.WELFARE: [
        "I'm currently dealing with some personal circumstances that are affecting my studies.",
        "I wanted to ask about what kind of support might be available right now.",
        "I've been finding it difficult to keep up with my coursework recently.",
        "I'm hoping to get some advice about support services that might help.",
        "I wanted to reach out because I'm struggling a bit and not sure what support is available.",
    ],
    Ticket.Category.CAREERS: [
        "I'm starting to think about my career options and wanted some guidance.",
        "I wanted to ask about resources available for career planning.",
        "I'm interested in learning more about internship opportunities.",
        "Could someone point me towards careers support or advice?",
        "I'm starting to prepare applications and would appreciate some guidance.",
    ],
    Ticket.Category.FINANCIAL_ISSUES: [
        "I'm experiencing some financial difficulties and wanted to ask about possible support.",
        "I wanted to check if there are any financial assistance options available.",
        "I'm looking for advice about managing finances during my studies.",
        "I have a question about funding options that might apply to me.",
        "Could someone advise me about financial support available to students?",
    ],
    Ticket.Category.UNI_PROCEDURES_REGULATIONS: [
        "I'm trying to understand how a particular university regulation applies in my situation.",
        "I had a question about a university procedure and wanted some clarification.",
        "I'm not sure what the correct process is for this situation.",
        "Could someone explain the relevant university policy for this?",
        "I'm looking for guidance on how to follow the correct university procedure.",
    ],
    Ticket.Category.ADMINISTRATION: [
        "I noticed something in my student record that might need updating.",
        "I wanted to ask about an administrative issue related to my student details.",
        "Some information linked to my account doesn't seem correct.",
        "I have a question regarding an administrative process.",
        "Could someone help me resolve a small administrative issue?",
    ],
    Ticket.Category.APPEALS_COMPLAINTS_AND_MISCONDUCT: [
        "I wanted to ask about the process for raising an academic appeal.",
        "I'm looking for guidance on how to submit a complaint.",
        "I had a question about the procedure for raising a concern.",
        "I'm unsure about the steps involved in submitting an appeal.",
        "Could someone explain the process for handling academic complaints?",
    ],
    Ticket.Category.DIGNITY_AND_INCLUSION: [
        "I wanted to raise a concern related to inclusivity.",
        "I'm looking for advice about a situation that made me uncomfortable.",
        "I wanted to ask about how to report an issue related to dignity and inclusion.",
        "Could someone advise me on how to address a concern about inclusivity?",
        "I would appreciate guidance on how to raise this type of concern.",
    ],
    Ticket.Category.DISABILITY_SUPPORT: [
        "I'm interested in learning about disability support services.",
        "I wanted to ask about academic adjustments that might be available.",
        "Could someone advise me about support for students with disabilities?",
        "I'm looking for information about how to access disability support.",
        "I wanted to check what support options exist for accessibility needs.",
    ],
    Ticket.Category.DOCUMENT_AND_LETTER_REQUESTS: [
        "I need to request a document confirming my student status.",
        "Could someone advise how to obtain an official letter from the university?",
        "I'm looking to request documentation related to my enrolment.",
        "I need an official letter for administrative purposes.",
        "Could someone guide me through requesting a student document?",
    ],
    Ticket.Category.FEES_FUNDING_AND_MONEY_ADVICE: [
        "I wanted to ask about funding options available to students.",
        "I'm looking for advice about tuition fees and financial support.",
        "Could someone explain what funding opportunities might apply to me?",
        "I have a question about financial support during my studies.",
        "I'm trying to understand the funding options available.",
    ],
    Ticket.Category.GRADUATION: [
        "I wanted to ask about the graduation process.",
        "I'm looking for information about graduation eligibility.",
        "Could someone explain the next steps before graduation?",
        "I had a question regarding the graduation timeline.",
        "I'm trying to understand what I need to do before graduating.",
    ],
    Ticket.Category.HEALTH_AND_WELLBEING: [
        "I'm looking for information about health and wellbeing services.",
        "I wanted to ask about support available for student wellbeing.",
        "Could someone guide me to the appropriate wellbeing services?",
        "I'm interested in learning about wellbeing resources available.",
        "I wanted to ask about support related to health and wellbeing.",
    ],
    Ticket.Category.HOUSING_AND_ACCOMMODATION_SUPPORT: [
        "I'm having an issue related to accommodation and wanted some advice.",
        "Could someone help me understand the housing options available?",
        "I wanted to ask about support with accommodation.",
        "I'm looking for guidance regarding housing support.",
        "I have a question about accommodation arrangements.",
    ],
    Ticket.Category.INDUSTRIAL_ACTION: [
        "I wanted to ask how the current industrial action might affect my studies.",
        "Some of my teaching sessions have been disrupted and I'm unsure what to expect.",
        "Could someone clarify how industrial action affects scheduled teaching?",
        "I'm wondering what impact the strikes might have on my modules.",
        "I had a question about how disruptions might affect coursework or teaching.",
    ],
    Ticket.Category.NEW_STUDENTS: [
        "I'm a new student and had a few questions about getting started.",
        "Could someone guide me through the first steps of starting my programme?",
        "I'm looking for information that might help new students settle in.",
        "I wanted to ask about resources available for new students.",
        "I'm just getting started and wanted some guidance.",
    ],
    Ticket.Category.RETURNING_TO_STUDY: [
        "I'm planning to return to my studies and wanted some guidance.",
        "I wanted to ask about the process for returning to my programme.",
        "I'm hoping to resume my studies and wanted to understand the steps involved.",
        "Could someone advise me about returning after a break?",
        "I wanted to ask what I need to do to return to my course.",
    ],
    Ticket.Category.STUDENT_LIFE: [
        "I'm interested in learning more about student activities.",
        "Could someone point me toward information about societies?",
        "I wanted to ask about opportunities to get involved in student life.",
        "I'm curious about extracurricular activities available to students.",
        "Could someone guide me to resources about student events?",
    ],
    Ticket.Category.VISAS_IMMIGRATION_AND_SUPPORT: [
        "I had a question about visa requirements during my studies.",
        "I'm looking for guidance regarding immigration support.",
        "Could someone advise me about visa-related responsibilities?",
        "I wanted to ask about maintaining visa compliance.",
        "I'm seeking information about visa documentation.",
    ],
    Ticket.Category.OTHER: [
        "I have a general question and wasn't sure who to ask.",
        "I'm looking for some guidance on a situation I'm facing.",
        "I wanted to ask for advice about something related to my studies.",
        "Could someone point me in the right direction?",
        "I'm hoping to get some guidance on what I should do next.",
    ],
}

GENERIC_STUDENT_COMMENTS = [
    "Just checking in to see if there are any updates on this.",
    "Please let me know if you need any additional information from me.",
    "I'm still experiencing the same issue and wanted to follow up.",
    "Thanks for looking into this, I appreciate the help.",
    "I just wanted to check what the next steps might be.",
]

COMMENT_AND_REPLY_BY_CATEGORY = {
    Ticket.Category.ASSESSMENT: [
        {
            "staff": "Could you confirm which assessment or module this relates to?",
            "student": "It relates to an assessment in one of my current modules.",
        },
        {
            "staff": "Could you clarify the issue you encountered during the assessment process?",
            "student": "I'm having difficulty completing the required steps for the assessment.",
        },
        {
            "staff": "Please confirm the deadline you are working towards.",
            "student": "The deadline is approaching soon so I wanted to check.",
        },
        {
            "staff": "Could you provide a bit more detail about what happened when you attempted the assessment?",
            "student": "Sure, I can explain what happened when I tried to complete it.",
        },
    ],
    Ticket.Category.WELFARE: [
        {
            "staff": "Would you like guidance on available welfare or support services?",
            "student": "Yes, I would appreciate guidance on what support options are available.",
        },
        {
            "staff": "Is this currently affecting your ability to keep up with your studies?",
            "student": "Yes, it has been affecting my ability to focus on coursework.",
        },
        {
            "staff": "Would you prefer to discuss this with a support adviser?",
            "student": "Yes, that would be helpful if possible.",
        },
        {
            "staff": "Would you like us to share some relevant support resources?",
            "student": "Yes, that would be very helpful.",
        },
    ],
    Ticket.Category.CAREERS: [
        {
            "staff": "Could you confirm what type of careers support you are looking for?",
            "student": "I'm mainly looking for advice about preparing applications.",
        },
        {
            "staff": "Are you currently exploring internships or graduate roles?",
            "student": "I'm currently exploring both options.",
        },
        {
            "staff": "Would you like support reviewing your CV or applications?",
            "student": "Yes, that would be very helpful.",
        },
        {
            "staff": "Could you clarify what stage you are at with your applications?",
            "student": "I'm currently preparing applications and researching opportunities.",
        },
    ],
    Ticket.Category.FINANCIAL_ISSUES: [
        {
            "staff": "Could you clarify whether your concern relates to tuition fees or general finances?",
            "student": "It mainly relates to managing my finances during term time.",
        },
        {
            "staff": "Would you like guidance on available financial support?",
            "student": "Yes, I would appreciate advice on support options.",
        },
        {
            "staff": "Have you explored any funding opportunities already?",
            "student": "Not yet, I wanted to understand what options are available first.",
        },
        {
            "staff": "Would you like information about financial assistance schemes?",
            "student": "Yes, that information would be very helpful.",
        },
    ],
    Ticket.Category.UNI_PROCEDURES_REGULATIONS: [
        {
            "staff": "Could you clarify which regulation or procedure you are referring to?",
            "student": "I'm trying to understand the correct process I should follow.",
        },
        {
            "staff": "Please provide a bit of context so we can advise accurately.",
            "student": "Sure, I can explain the situation and what I'm unsure about.",
        },
        {
            "staff": "Is your question about a university policy or a programme-specific rule?",
            "student": "It's about a university policy and how it applies in my situation.",
        },
        {
            "staff": "What outcome are you hoping to achieve so we can direct you correctly?",
            "student": "I mainly want to make sure I'm following the correct procedure.",
        },
    ],
    Ticket.Category.ADMINISTRATION: [
        {
            "staff": "Could you confirm which administrative detail needs to be updated?",
            "student": "Some information in my records appears to be incorrect.",
        },
        {
            "staff": "Please clarify what information you are trying to change.",
            "student": "I'm trying to make sure my details are recorded correctly.",
        },
        {
            "staff": "Does this issue affect your student record or personal details?",
            "student": "It appears to affect my student record.",
        },
        {
            "staff": "Could you confirm what the correct information should be?",
            "student": "Yes, I can provide the correct details if needed.",
        },
    ],
    Ticket.Category.APPEALS_COMPLAINTS_AND_MISCONDUCT: [
        {
            "staff": "Could you clarify whether you are seeking advice on an appeal or complaint?",
            "student": "I'm looking for guidance on the correct process.",
        },
        {
            "staff": "Please confirm if you are looking for procedural guidance.",
            "student": "Yes, I want to understand what steps I should take.",
        },
        {
            "staff": "Could you provide some background about the situation?",
            "student": "Yes, I can give some more context if that helps.",
        },
        {
            "staff": "Let us know what outcome you are hoping to achieve.",
            "student": "I'd like to understand what options are available to me.",
        },
    ],
    Ticket.Category.DIGNITY_AND_INCLUSION: [
        {
            "staff": "Would you like guidance on how to raise this concern?",
            "student": "Yes, I'd appreciate advice on how best to proceed.",
        },
        {
            "staff": "Please let us know if you would like support resources.",
            "student": "Yes, information on available support would be helpful.",
        },
        {
            "staff": "Could you clarify whether this relates to a specific situation?",
            "student": "Yes, it's about something that happened recently.",
        },
        {
            "staff": "Let us know if you would like assistance with reporting this concern.",
            "student": "Yes, I'd like some guidance on how to report it.",
        },
    ],
    Ticket.Category.DISABILITY_SUPPORT: [
        {
            "staff": "Could you clarify what type of support you are looking for?",
            "student": "I'm interested in understanding what adjustments might be available.",
        },
        {
            "staff": "Do you currently have any support arrangements in place?",
            "student": "No, this would be a new request for support.",
        },
        {
            "staff": "Would you like guidance on arranging academic adjustments?",
            "student": "Yes, I would appreciate guidance on that.",
        },
        {
            "staff": "Would you like help accessing disability support services?",
            "student": "Yes, that would be helpful.",
        },
    ],
    Ticket.Category.DOCUMENT_AND_LETTER_REQUESTS: [
        {
            "staff": "Could you confirm which document you require?",
            "student": "I need a document confirming my student status.",
        },
        {
            "staff": "Please clarify what the document will be used for.",
            "student": "It will be used for administrative purposes.",
        },
        {
            "staff": "Do you require the document urgently?",
            "student": "It would be helpful to receive it soon if possible.",
        },
        {
            "staff": "Could you confirm what information needs to be included in the letter?",
            "student": "It needs to confirm my enrolment details.",
        },
    ],
    Ticket.Category.FEES_FUNDING_AND_MONEY_ADVICE: [
        {
            "staff": "Could you confirm whether your question relates to fees or funding?",
            "student": "It relates mainly to funding options.",
        },
        {
            "staff": "Please clarify what type of financial advice you are seeking.",
            "student": "I'm looking for guidance on available financial support.",
        },
        {
            "staff": "Could you confirm your situation so we can advise appropriately?",
            "student": "Yes, I can provide more details if needed.",
        },
        {
            "staff": "Would you like information about funding opportunities?",
            "student": "Yes, that would be helpful.",
        },
    ],
    Ticket.Category.GRADUATION: [
        {
            "staff": "Could you confirm what information you need regarding graduation?",
            "student": "I'm looking for clarification about the graduation process.",
        },
        {
            "staff": "Please confirm your expected completion date.",
            "student": "I can confirm my expected completion date if needed.",
        },
        {
            "staff": "Let us know if your enquiry relates to registration or eligibility.",
            "student": "I'd like clarification on whether I'm eligible.",
        },
        {
            "staff": "Could you clarify what part of the graduation process you need help with?",
            "student": "I'm mainly trying to understand the next steps.",
        },
    ],
    Ticket.Category.HEALTH_AND_WELLBEING: [
        {
            "staff": "Would you like information about wellbeing support services?",
            "student": "Yes, I would appreciate information about what support is available.",
        },
        {
            "staff": "Please let us know if you would like help accessing support.",
            "student": "Yes, I would like guidance on how to access those services.",
        },
        {
            "staff": "Could you clarify what type of support you are seeking?",
            "student": "I'm looking for information about available wellbeing services.",
        },
        {
            "staff": "Let us know if you would like us to signpost support resources.",
            "student": "Yes, that would be helpful.",
        },
    ],
    Ticket.Category.HOUSING_AND_ACCOMMODATION_SUPPORT: [
        {
            "staff": "Could you confirm whether this relates to university accommodation?",
            "student": "Yes, it's related to accommodation and I need some advice.",
        },
        {
            "staff": "Please clarify the type of housing support you need.",
            "student": "I'm looking for guidance on what housing options are available.",
        },
        {
            "staff": "Could you confirm whether the situation is urgent?",
            "student": "At the moment I'm mainly seeking advice.",
        },
        {
            "staff": "Let us know if you need help understanding housing options.",
            "student": "Yes, I would appreciate guidance on that.",
        },
    ],
    Ticket.Category.INDUSTRIAL_ACTION: [
        {
            "staff": "Could you confirm which teaching activities were affected?",
            "student": "Some of my scheduled sessions were disrupted.",
        },
        {
            "staff": "Please clarify how this disruption has affected you.",
            "student": "It has affected some of the teaching sessions for my module.",
        },
        {
            "staff": "Let us know if your concern relates to teaching or assessments.",
            "student": "I'm mainly concerned about the impact on teaching.",
        },
        {
            "staff": "Could you confirm which modules are affected?",
            "student": "I can confirm the modules if that helps.",
        },
    ],
    Ticket.Category.NEW_STUDENTS: [
        {
            "staff": "Welcome. Could you confirm what information you are looking for?",
            "student": "I'm looking for guidance on getting started with my studies.",
        },
        {
            "staff": "Please let us know if you need help accessing services.",
            "student": "Yes, I'd appreciate some help with that.",
        },
        {
            "staff": "Could you confirm whether you have completed enrolment?",
            "student": "I'm currently working through the enrolment steps.",
        },
        {
            "staff": "Let us know if you need help navigating university systems.",
            "student": "Yes, some guidance would definitely help.",
        },
    ],
    Ticket.Category.RETURNING_TO_STUDY: [
        {
            "staff": "Could you confirm when you last studied on your programme?",
            "student": "I've been away from my studies for a while.",
        },
        {
            "staff": "Please clarify whether you plan to return to the same programme.",
            "student": "Yes, I'm hoping to return to the same programme.",
        },
        {
            "staff": "Could you confirm what guidance you are looking for?",
            "student": "I'd like to understand the process for returning.",
        },
        {
            "staff": "Let us know if you need help with re-enrolment.",
            "student": "Yes, that would be very helpful.",
        },
    ],
    Ticket.Category.STUDENT_LIFE: [
        {
            "staff": "Could you confirm what type of activities you are interested in?",
            "student": "I'm interested in student activities and events.",
        },
        {
            "staff": "Are you looking for information about societies or campus events?",
            "student": "Both would be helpful.",
        },
        {
            "staff": "Would you like guidance on getting involved in student groups?",
            "student": "Yes, that would be useful.",
        },
        {
            "staff": "Could you clarify whether you are interested in on-campus activities?",
            "student": "Yes, I'd like to learn more about them.",
        },
    ],
    Ticket.Category.VISAS_IMMIGRATION_AND_SUPPORT: [
        {
            "staff": "Could you confirm what aspect of visa support you need help with?",
            "student": "I need guidance on visa compliance requirements.",
        },
        {
            "staff": "Please clarify whether your enquiry relates to documentation.",
            "student": "Yes, it's about documentation requirements.",
        },
        {
            "staff": "Could you confirm what information you are looking for?",
            "student": "I'd like guidance on the correct process.",
        },
        {
            "staff": "Let us know if your question relates to maintaining visa status.",
            "student": "Yes, I want to make sure I remain compliant.",
        },
    ],
    Ticket.Category.OTHER: [
        {
            "staff": "Thank you for your message. Could you clarify what outcome you are hoping for so we can direct this appropriately?",
            "student": "I'm looking for guidance on what to do next and who the right team would be.",
        },
        {
            "staff": "Could you provide a little more detail about your enquiry?",
            "student": "Yes, I can provide additional information if needed.",
        },
        {
            "staff": "Please clarify what kind of assistance you are looking for.",
            "student": "I'm mainly looking for advice on how to proceed.",
        },
        {
            "staff": "Could you explain the situation in a bit more detail?",
            "student": "Sure, I can expand on the situation.",
        },
    ],
}


def generate_subject_and_body(*, faculty, study_level, category):
    subject = (
        random.choice(SUBJECTS_BY_CATEGORY.get(category, ["General enquiry"]))
        + " for "
        + faculty.upper()
    )

    faculty_text = random.choice(FACULTY_BODY.get(faculty, [""])).strip()
    level_text = random.choice(STUDY_LEVEL_BODY.get(study_level, [""])).strip()
    category_text = random.choice(CATEGORY_BODY.get(category, [""])).strip()

    body = f"{faculty_text} {level_text} {category_text}"

    return subject, body


def generate_standalone_student_comment(category):
    comments = (
        STANDALONE_STUDENT_COMMENTS_BY_CATEGORY.get(category, [])
        + GENERIC_STUDENT_COMMENTS
    )
    return random.choice(comments)


def generate_comment_and_response_by_category(category, probability_of_response=0.33):
    comment_and_reply = random.choice(COMMENT_AND_REPLY_BY_CATEGORY.get(category, []))
    staff_comment = comment_and_reply.get("staff", "").strip()
    # default of 1/3 chance of no student reply
    if random.random() < probability_of_response:
        student_comment = ""
    else:
        student_comment = comment_and_reply.get("student", "").strip()
    return staff_comment, student_comment
