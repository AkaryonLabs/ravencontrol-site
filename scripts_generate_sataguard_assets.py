from PIL import Image, ImageDraw, ImageFont, ImageFilter
from pathlib import Path
import math

OUT = Path('assets')
OUT.mkdir(exist_ok=True)

NAVY = (7, 17, 31)
NAVY2 = (13, 29, 48)
BLUE = (39, 168, 255)
BLUE2 = (24, 103, 184)
GOLD = (216, 170, 79)
AMBER = (215, 155, 47)
GREEN = (20, 122, 77)
SILVER = (226, 234, 244)
SOFT = (244, 247, 251)
TEXT = (18, 25, 37)
MUTED = (93, 108, 128)
WHITE = (255, 255, 255)
LINE = (214, 224, 235)


def font(size, bold=False):
    names = [
        '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf' if bold else '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
        '/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf' if bold else '/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf',
    ]
    for n in names:
        try:
            return ImageFont.truetype(n, size)
        except Exception:
            pass
    return ImageFont.load_default()


def rounded(draw, box, r, fill, outline=None, width=1):
    draw.rounded_rectangle(box, radius=r, fill=fill, outline=outline, width=width)


def gradient_bg(w, h, c1=NAVY, c2=(10, 32, 55)):
    img = Image.new('RGB', (w, h), c1)
    pix = img.load()
    for y in range(h):
        for x in range(w):
            t = (x/w*0.55 + y/h*0.45)
            # soft blue glow
            glow = math.exp(-(((x-w*0.78)/(w*0.32))**2 + ((y-h*0.22)/(h*0.28))**2))
            col = tuple(int(c1[i]*(1-t)+c2[i]*t + BLUE[i]*0.18*glow) for i in range(3))
            pix[x,y] = tuple(max(0,min(255,v)) for v in col)
    return img


def shield_mark(draw, x, y, s, accent=BLUE):
    # simple shield outline + signal bars, brand-safe no old raven
    pts = [(x+s*0.5,y), (x+s*0.88,y+s*0.16), (x+s*0.82,y+s*0.62), (x+s*0.5,y+s), (x+s*0.18,y+s*0.62), (x+s*0.12,y+s*0.16)]
    draw.polygon(pts, fill=(14,33,56), outline=accent)
    # inner S-like path / triage signal
    w=max(3,int(s*0.055))
    draw.arc([x+s*.28,y+s*.24,x+s*.72,y+s*.58], 200, 20, fill=GOLD, width=w)
    draw.arc([x+s*.28,y+s*.42,x+s*.72,y+s*.76], 20, 200, fill=GOLD, width=w)
    for i,bar in enumerate([.25,.38,.51,.64]):
        draw.line([(x+s*.30+i*s*.11,y+s*.82),(x+s*.30+i*s*.11,y+s*.88)], fill=accent, width=w)


def text(draw, xy, s, size, fill=TEXT, bold=False, anchor=None):
    draw.text(xy, s, font=font(size, bold), fill=fill, anchor=anchor)


def card(draw, box, title, body=None, icon=None, accent=BLUE):
    rounded(draw, box, 22, WHITE, LINE, 2)
    x1,y1,x2,y2=box
    if icon:
        rounded(draw, (x1+24,y1+24,x1+86,y1+86), 31, accent, None)
        text(draw, (x1+55,y1+55), icon, 30, WHITE, True, 'mm')
        tx=x1+106
    else:
        tx=x1+28
    text(draw, (tx,y1+30), title, 28, TEXT, True)
    if body:
        # wrap simple
        words=body.split(); lines=[]; cur=''
        max_chars=max(24,int((x2-tx-26)/14))
        for w in words:
            if len(cur)+len(w)+1>max_chars:
                lines.append(cur); cur=w
            else:
                cur=(cur+' '+w).strip()
        if cur: lines.append(cur)
        for i,line in enumerate(lines[:3]):
            text(draw, (tx,y1+68+i*27), line, 20, MUTED)


def desktop():
    w,h=1536,1024
    img=Image.new('RGB',(w,h),SOFT)
    d=ImageDraw.Draw(img)
    # sidebar
    rounded(d,(0,0,285,h),0,NAVY)
    shield_mark(d,32,48,76)
    text(d,(122,54),'SataGuard',40,WHITE,True)
    text(d,(122,104),'Scam triage before you act.',18,GOLD)
    for i,(name,ic) in enumerate([('SataCheck','✓'),('SataCircle','◎'),('SataBusiness','$'),('SataCompanion','★')]):
        y=205+i*86
        fill=(19,44,71) if i else (18,88,145)
        rounded(d,(22,y,263,y+64),14,fill,None)
        text(d,(55,y+32),ic,28,WHITE,True,'mm')
        text(d,(88,y+22),name,22,WHITE,True)
    rounded(d,(24,820,262,948),16,(15,36,58),(75,94,116),2)
    shield_mark(d,44,846,44)
    text(d,(96,848),'Pause. Triage. Verify.',17,WHITE,True)
    text(d,(96,878),'A calm second look',16,SILVER)
    text(d,(96,902),'before digital damage.',16,SILVER)

    # header
    text(d,(330,46),'Welcome back, John',44,TEXT,True)
    text(d,(330,102),'A trusted pause before risky digital decisions.',24,MUTED)
    rounded(d,(1248,32,1508,100),18,WHITE,LINE,2)
    text(d,(1315,50),'John Doe',22,TEXT,True)
    text(d,(1315,76),'Protected profile',18,MUTED)
    rounded(d,(1266,48,1298,80),16,BLUE,None)
    text(d,(1282,64),'J',18,WHITE,True,'mm')

    # main hero check card
    rounded(d,(820,140,1508,410),22,(255,252,246),(231,211,171),2)
    text(d,(870,188),'Need to check something?',34,TEXT,True)
    text(d,(870,242),'Before you click, pay, reply, or share a code,',23,(44,54,69))
    text(d,(870,275),'send it to SataGuard for triage.',23,(44,54,69))
    rounded(d,(870,320,1190,382),14,(216,155,47),None)
    text(d,(1030,351),'Start a SataCheck',25,WHITE,True,'mm')
    shield_mark(d,1310,178,130)
    
    # guardian card
    rounded(d,(310,140,792,410),22,WHITE,LINE,2)
    text(d,(338,166),'Your Digital Guardian',24,TEXT,True)
    rounded(d,(356,205,476,325),60,(231,239,248),None)
    text(d,(416,265),'M',54,BLUE2,True,'mm')
    text(d,(510,212),'Guardian Mia',30,TEXT,True)
    text(d,(510,252),'Human guidance when the risk feels personal.',20,MUTED)
    rounded(d,(338,345,762,386),12,(235,249,242),None)
    text(d,(372,354),'✓ Pause before you act.',20,GREEN,True)

    card(d,(310,438,666,584),'SataCheck','Submit one suspicious text, email, screenshot, link, or invoice.','?',BLUE2)
    card(d,(688,438,1044,584),'SataCircle','Protect parents, grandparents, caregivers, and household members.','◎',GREEN)
    card(d,(1066,438,1508,584),'SataBusiness','Review vendor changes, invoices, account warnings, and payment traps.','$',(74,70,180))

    rounded(d,(310,610,980,946),22,WHITE,LINE,2)
    text(d,(338,642),'Recent SataTriage activity',27,TEXT,True)
    rows=[('Urgent bank text reviewed','Use the official number on your card.','High risk',AMBER),('Suspicious invoice paused','Verify vendor through known contact.','Needs verification',BLUE2),('Family emergency message checked','Trusted contact confirmed safe.','Resolved',GREEN)]
    for i,(a,b,c,col) in enumerate(rows):
        y=696+i*78
        rounded(d,(338,y,382,y+44),22,col,None)
        text(d,(360,y+22),'✓',22,WHITE,True,'mm')
        text(d,(405,y-2),a,21,TEXT,True)
        text(d,(405,y+26),b,18,MUTED)
        text(d,(810,y+10),c,17,col,True)
        d.line((338,y+62,942,y+62),fill=(232,237,243),width=1)

    rounded(d,(1004,610,1508,760),22,(239,247,255),(190,215,242),2)
    shield_mark(d,1046,642,90)
    text(d,(1160,642),'Your plan: SataCompanion',25,BLUE2,True)
    text(d,(1160,684),'AI review + human Guardian support',20,(44,54,69))
    text(d,(1160,716),'for digital-risk moments.',20,(44,54,69))
    rounded(d,(1004,790,1508,946),22,(255,248,237),(236,213,173),2)
    text(d,(1050,836),'Pause the pressure.',33,TEXT,True)
    text(d,(1050,884),'Check first. Act safer.',23,MUTED)
    img.save(OUT/'customer-desktop.png', quality=95)


def phone():
    w,h=856,1837
    img=Image.new('RGB',(w,h),(5,8,12))
    d=ImageDraw.Draw(img)
    # phone shell
    rounded(d,(18,18,w-18,h-18),82,(18,19,22),(65,65,70),5)
    rounded(d,(45,55,w-45,h-55),58,SOFT,None)
    d.rounded_rectangle((330,64,526,112),radius=28,fill=(5,8,12))
    text(d,(100,88),'9:41',28,TEXT,True)
    text(d,(690,88),'▮▮  WiFi  ▱',20,TEXT,True)
    # header
    shield_mark(d,74,152,82)
    text(d,(178,158),'SataGuard',42,TEXT,True)
    text(d,(178,206),'Scam triage before you act.',22,MUTED)
    rounded(d,(590,154,666,230),38,(230,238,247),None)
    text(d,(628,192),'M',34,BLUE2,True,'mm')
    text(d,(688,164),'Guardian Mia',24,TEXT,True)
    text(d,(688,198),'Here for you',20,MUTED)
    # hero
    rounded(d,(66,270,790,700),24,(255,252,247),(232,215,183),2)
    text(d,(122,318),'Need to check',42,TEXT,True)
    text(d,(122,366),'something?',42,TEXT,True)
    text(d,(122,434),'Pause before you click, pay,',24,(55,65,80))
    text(d,(122,468),'reply, or share a code.',24,(55,65,80))
    shield_mark(d,560,332,150)
    rounded(d,(116,584,740,660),18,AMBER,None)
    text(d,(428,622),'Start a SataCheck',32,WHITE,True,'mm')
    
    y=730
    items=[('SataCheck','Send a screenshot, text, email, or link.','? ',BLUE2),('SataCircle','Protect family with trusted contacts.','◎',GREEN),('SataBusiness','Pause invoice and payment traps.','$',(74,70,180))]
    for title,body,ic,col in items:
        rounded(d,(66,y,790,y+150),20,WHITE,LINE,2)
        rounded(d,(94,y+34,176,y+116),41,col,None)
        text(d,(135,y+75),ic.strip(),32,WHITE,True,'mm')
        text(d,(220,y+36),title,32,TEXT,True)
        text(d,(220,y+82),body,22,MUTED)
        text(d,(736,y+74),'›',46,MUTED,False,'mm')
        y += 176
    rounded(d,(66,y+4,790,y+270),20,WHITE,LINE,2)
    text(d,(96,y+38),'Recent SataTriage',30,TEXT,True)
    text(d,(660,y+42),'View all',20,BLUE2,True)
    text(d,(116,y+112),'✓',30,GREEN,True)
    text(d,(174,y+94),'Suspicious text reviewed',25,TEXT,True)
    text(d,(174,y+128),'Verify through official bank number.',21,MUTED)
    text(d,(600,y+114),'Today',18,MUTED)
    text(d,(116,y+198),'✓',30,GREEN,True)
    text(d,(174,y+180),'Screenshot attached',25,TEXT,True)
    text(d,(174,y+214),'SataGuard triaged the risk.',21,MUTED)
    # bottom CTA
    rounded(d,(66,1540,790,1680),22,(255,248,237),(236,213,173),2)
    text(d,(118,1586),'Human guidance available',28,TEXT,True)
    text(d,(118,1626),'AI review. Guardian support. Safer decisions.',20,MUTED)
    rounded(d,(570,1594,748,1648),16,(235,249,242),None)
    text(d,(659,1621),'Protected',18,GREEN,True,'mm')
    # tab bar
    rounded(d,(45,1714,w-45,1812),0,WHITE,None)
    for i,(lbl,ic) in enumerate([('Home','⌂'),('Check','✓'),('Circle','◎'),('Help','?')]):
        x=130+i*190
        col=AMBER if i==0 else (70,78,90)
        text(d,(x,1744),ic,32,col,True,'mm')
        text(d,(x,1782),lbl,18,col,True,'mm')
    img.save(OUT/'customer-phone.png', quality=95)


def memory():
    w,h=1600,980
    img=Image.new('RGB',(w,h),SOFT)
    d=ImageDraw.Draw(img)
    rounded(d,(36,36,w-36,h-36),30,WHITE,LINE,2)
    rounded(d,(66,66,w-66,172),24,NAVY,None)
    shield_mark(d,98,92,54)
    text(d,(170,90),'SataVault Memory',40,WHITE,True)
    text(d,(170,134),'Trusted context for scam triage and Guardian follow-up.',22,SILVER)
    rounded(d,(1190,92,1408,136),22,AMBER,None)
    text(d,(1299,114),'Companion profile',22,WHITE,True,'mm')
    rounded(d,(1412,92,1530,136),22,BLUE2,None)
    text(d,(1471,114),'High care',21,WHITE,True,'mm')

    def panel(box,title,accent=BLUE):
        rounded(d,box,18,WHITE,LINE,2)
        x1,y1,x2,y2=box
        rounded(d,(x1+26,y1+26,x1+38,y1+70),6,accent,None)
        text(d,(x1+54,y1+28),title,28,TEXT,True)
    panel((88,214,548,500),'Protected Person',AMBER)
    rounded(d,(124,290,216,382),46,(255,232,232),None)
    text(d,(170,336),'LC',30,(190,25,32),True,'mm')
    text(d,(244,292),'Linda Carter',38,TEXT,True)
    text(d,(244,338),'Age 78 • SataCompanion',22,MUTED)
    text(d,(122,424),'Prefers phone calls. Daughter receives',20,TEXT)
    text(d,(122,452),'high-risk alerts before action.',20,TEXT)

    panel((588,214,1528,500),'Trusted Contacts And Rules',BLUE2)
    contacts=[('M','Maya Carter','Daughter - call/text for High or Critical alerts',BLUE2),('T','Tyler Carter','Grandson - verified family emergency contact',GREEN)]
    for i,(init,name,desc,col) in enumerate(contacts):
        y=292+i*92
        rounded(d,(626,y,690,y+64),32,col,None)
        text(d,(658,y+32),init,28,WHITE,True,'mm')
        text(d,(710,y+0),name,26,TEXT,True)
        text(d,(710,y+34),desc,18,MUTED)
        rounded(d,(1122,y+14,1238,y+54),20,(236,241,247),None)
        text(d,(1180,y+34),'Trusted',20,TEXT,True,'mm')

    panel((88,540,548,888),'Risk History',AMBER)
    risks=[('Bank impersonation text','Reviewed May 28 • High risk'),('Package delivery scam','Reviewed June 2 • Medium risk'),('Unknown tech support call','Reviewed June 8 • Critical risk')]
    for i,(a,b) in enumerate(risks):
        y=616+i*84
        rounded(d,(124,y,512,y+58),14,(255,248,237),(238,201,139),1)
        text(d,(148,y+12),a,22,TEXT,True)
        text(d,(148,y+38),b,18,MUTED)

    panel((588,540,1030,888),'Protection Rules',GREEN)
    rules=['No gift cards for callers.','Never share security codes.','Verify emergencies through Maya.','No wire, crypto, or Zelle until reviewed.']
    for i,r in enumerate(rules):
        y=616+i*60
        rounded(d,(626,y,984,y+48),14,(235,249,242),(188,224,206),1)
        text(d,(650,y+13),r,18,TEXT)

    panel((1068,540,1528,888),'Next Guardian Action',(204,29,45))
    rounded(d,(1106,616,1492,776),18,(255,238,239),(248,183,188),2)
    text(d,(1136,648),'Call Linda before noon',26,TEXT,True)
    text(d,(1136,688),'Review tech support call. Remind her',20,TEXT)
    text(d,(1136,718),'not to install remote access tools.',20,TEXT)
    rounded(d,(1136,798,1410,842),22,NAVY,None)
    text(d,(1273,820),'Guardian Mia assigned',21,WHITE,True,'mm')
    text(d,(1136,866),'SataGuard remembers the pattern.',18,MUTED)

    rounded(d,(86,912,1518,948),18,(235,240,246),None)
    text(d,(116,920),'Memory fields: trusted contacts • past scams • approved vendors • family rules • payment policies',18,MUTED)
    text(d,(1336,920),'SataGuard',20,TEXT,True)
    img.save(OUT/'axiom-memory.png', quality=95)

if __name__ == '__main__':
    desktop(); phone(); memory()
    print('Generated SataGuard PNG assets.')
