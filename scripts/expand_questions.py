import json

with open('/Users/btmacstudio/.openclaw/workspace/projects/hukuk-ai/configs/evaluation/test_questions.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

data['_meta']['total_questions'] = 50
data['_meta']['categories'].update({
    "tbk_satis": "TBK Satış Sözleşmesi",
    "tbk_eser": "TBK Eser Sözleşmesi",
    "tbk_kefalet": "TBK Kefalet Sözleşmesi",
    "tmk_esya": "TMK Eşya Hukuku (YİM Hazırlık - Kapsam Dışı)",
    "tmk_aile": "TMK Aile Hukuku (YİM Hazırlık - Kapsam Dışı)"
})

new_questions = [
    {
        "id": f"TBK-{str(i).zfill(3)}",
        "question": q[0],
        "category": q[1],
        "difficulty": q[2],
        "expected_sources": q[3],
        "expected_keywords": q[4],
        "expected_answer_contains": q[5],
        "refusal_expected": q[6],
        "notes": q[7]
    }
    for i, q in enumerate([
        ("Satış sözleşmesinde satıcının ayıptan doğan sorumluluğu (ayıba karşı tekeffül) için alıcının gözden geçirme ve bildirim külfeti hangi sürelere tabidir?", "tbk_satis", "hard", ["TBK m.223"], ["gözden geçirme", "bildirim", "ayıp", "olağan akış", "hemen", "gecikmeksizin"], "gözden geçirme", False, "Ayıba karşı tekeffül bildirim külfeti"),
        ("Taksitle satış sözleşmesinin geçerliliği hangi şekil şartına bağlanmıştır?", "tbk_satis", "medium", ["TBK m.253"], ["yazılı", "şekil", "taksitle", "geçerlilik"], "yazılı", False, "Taksitle satış şekil şartı"),
        ("Eser sözleşmesinde yüklenicinin özen ve sadakat borcu TBK'da nasıl düzenlenmiştir?", "tbk_eser", "medium", ["TBK m.471"], ["yüklenici", "özen", "sadakat", "işçi", "hizmet sözleşmesi"], "özen", False, "Eser sözleşmesi yüklenici borcu"),
        ("Eser sözleşmesinde eserin beklenmedik hâl (mücbir sebep) nedeniyle yok olması durumunda hasara kim katlanır?", "tbk_eser", "hard", ["TBK m.483"], ["beklenmedik hâl", "hasar", "yüklenici", "teslim", "işsahibi", "kusur"], "yüklenici", False, "Eser sözleşmesi hasar dağılımı"),
        ("Kefalet sözleşmesinde eşin rızası hangi durumlarda aranmaz?", "tbk_kefalet", "hard", ["TBK m.584"], ["eşin rızası", "ticaret sicili", "esnaf", "meslek", "sanat", "şirket"], "ticaret sicili", False, "Kefalette eş rızası istisnaları"),
        ("TBK'ya göre müteselsil kefaletin şartları nelerdir?", "tbk_kefalet", "medium", ["TBK m.586"], ["müteselsil", "kefil", "el yazısı", "takip", "asıl borçlu"], "müteselsil", False, "Müteselsil kefalet"),
        ("Kusursuz sorumluluk hallerinden adam çalıştıranın sorumluluğunda kurtuluş kanıtı nasıl getirilir?", "tbk_haksiz_fiil", "hard", ["TBK m.66"], ["adam çalıştıran", "kurtuluş kanıtı", "özen", "seçmede", "talimat vermede", "denetlemede"], "özen", False, "Adam çalıştıranın sorumluluğu"),
        ("Bina malikinin sorumluluğunda, malikin rücu hakkı kime karşıdır?", "tbk_haksiz_fiil", "medium", ["TBK m.69"], ["bina maliki", "yapım bozukluğu", "bakım eksikliği", "rücu", "sorumlu olanlara"], "rücu", False, "Bina maliki sorumluluğu"),
        ("Sebepsiz zenginleşmeden doğan istem hakkı hangi sürelerde zamanaşımına uğrar?", "tbk_genel", "medium", ["TBK m.82"], ["sebepsiz zenginleşme", "iki yıl", "on yıl", "öğrenme", "zamanaşımı"], "iki yıl", False, "Sebepsiz zenginleşme zamanaşımı"),
        ("İfa zamanı taraflarca kararlaştırılmayan bir borç ne zaman muaccel olur?", "tbk_genel", "easy", ["TBK m.90"], ["muaccel", "hemen", "ifa", "derhâl", "kararlaştırılmadıkça"], "hemen", False, "Borcun muacceliyeti"),
        ("Alacaklının temerrüdü (alacaklı direnimi) hâlinde borçlu borcundan nasıl kurtulur?", "tbk_genel", "hard", ["TBK m.107", "TBK m.108"], ["alacaklı temerrüdü", "tevdi", "hakim", "sözleşmeden dönme", "satılarak"], "tevdi", False, "Alacaklı temerrüdü"),
        ("Borçlunun sorumlu olmadığı sonraki imkânsızlık (ifa imkânsızlığı) durumunda borç sona erer mi?", "tbk_genel", "medium", ["TBK m.136"], ["ifa imkânsızlığı", "sona erer", "borçlu", "kusur", "karşı edim", "sebepsiz zenginleşme"], "sona erer", False, "İfa imkânsızlığı"),
        ("Alacağın devri (temliki) sözleşmesinin geçerliliği hangi şekil şartına tabidir?", "tbk_genel", "medium", ["TBK m.183", "TBK m.184"], ["alacağın devri", "yazılı", "şekil", "geçerlilik", "temlik"], "yazılı", False, "Alacağın devri şekli"),
        ("Borcun üstlenilmesi (nakli) sözleşmesinde alacaklının rızası gerekir mi?", "tbk_genel", "medium", ["TBK m.195", "TBK m.196"], ["borcun üstlenilmesi", "alacaklı", "kabul", "onay", "iç üstlenme", "dış üstlenme"], "kabul", False, "Borcun üstlenilmesi"),
        ("TBK'ya göre takasın şartları nelerdir?", "tbk_genel", "medium", ["TBK m.143", "TBK m.144"], ["takas", "karşılıklı", "muaccel", "benzer", "tek taraflı", "beyan"], "muaccel", False, "Takas şartları"),
        ("Bağışlama vaadinin geçerliliği hangi şekil şartına bağlıdır?", "tbk_genel", "medium", ["TBK m.288"], ["bağışlama vaadi", "yazılı", "resmî", "taşınmaz"], "yazılı", False, "Bağışlama vaadi"),
        ("Geri alma hakkı saklı tutulan bağışlamada bağışlayan hangi hallerde bağışlamayı geri alabilir?", "tbk_genel", "hard", ["TBK m.295"], ["geri alma", "ağır suç", "aile ödevleri", "nafaka", "hukuka aykırı"], "ağır suç", False, "Bağışlamanın geri alınması"),
        ("Vekâletsiz iş görmede işgörenin sorumluluğu nasıldır?", "tbk_genel", "medium", ["TBK m.527"], ["vekâletsiz iş görme", "özen", "hafifletici", "kasıt", "ihmal", "zarar"], "özen", False, "Vekâletsiz iş görme"),
        ("Adi ortaklıkta ortakların idare hak ve yetkisi kime aittir?", "tbk_genel", "medium", ["TBK m.625"], ["adi ortaklık", "idare", "bütün ortaklar", "karar", "sözleşme"], "bütün ortaklar", False, "Adi ortaklık idaresi"),
        ("Ömür boyu gelir sözleşmesinin şekil şartı nedir?", "tbk_genel", "medium", ["TBK m.608"], ["ömür boyu gelir", "yazılı", "şekil", "resmî"], "yazılı", False, "Ömür boyu gelir sözleşmesi"),
        ("Genel işlem koşullarının (standart sözleşme şartları) yürürlüğe girmesi hangi şarta bağlanmıştır?", "tbk_genel", "hard", ["TBK m.21"], ["genel işlem koşulları", "kabul", "bilgi verme", "açıkça", "yürürlük"], "bilgi verme", False, "Genel işlem koşulları"),
        ("Sözleşmeden doğan hakların üçüncü kişiye etkisi (üçüncü kişi yararına sözleşme) nasıl işler?", "tbk_genel", "hard", ["TBK m.129"], ["üçüncü kişi", "yarar", "ifa", "isteme hakkı", "alacaklı"], "ifa", False, "Üçüncü kişi yararına sözleşme"),
        ("Manevi tazminat istemi TBK'nın hangi maddesinde düzenlenmiştir ve hangi durumlarda talep edilebilir?", "tbk_haksiz_fiil", "easy", ["TBK m.56", "TBK m.58"], ["manevi tazminat", "kişilik hakları", "bedensel bütünlük", "ölüm", "acı", "elem"], "kişilik hakları", False, "Manevi tazminat"),
        ("Müteselsil borçlulukta borçlulardan birinin ifası diğerlerini kurtarır mı?", "tbk_genel", "easy", ["TBK m.166"], ["müteselsil", "ifa", "kurtarır", "borçlu", "alacaklı"], "kurtarır", False, "Müteselsil borçluluk ifa"),
        ("Garantörlük (garanti sözleşmesi) ile kefalet sözleşmesi arasındaki temel fark nedir?", "tbk_genel", "hard", ["TBK m.128", "TBK m.582"], ["garanti", "kefalet", "bağımsız", "feri", "asıl borç"], "bağımsız", False, "Garanti vs kefalet"),
        ("Kira sözleşmesinde kiralananın kullanım hakkı (alt kira) bir başkasına devredilebilir mi?", "tbk_kira", "medium", ["TBK m.322"], ["alt kira", "kullanım hakkı", "onay", "yazılı rıza", "konut"], "yazılı rıza", False, "Alt kira"),
        ("Taşınır rehni (teslimsiz rehin) Türk Medeni Kanunu'na göre mümkün müdür?", "tmk_esya", "hard", ["TMK m.940"], ["taşınır rehni", "teslim", "zilyetlik", "istisna"], "teslim", True, "Faz 1 kapsamında TBK odaklı, TMK detayları kapsam dışı kalabilir (YİM hazırlık)."),
        ("TMK'ya göre iyiniyet karinesi nedir ve hangi maddede düzenlenmiştir?", "tmk_genel", "medium", ["TMK m.3"], ["iyiniyet", "karine", "hakların kazanılması", "asıl"], "karine", True, "TMK genel ilke (YİM hazırlık)."),
        ("TMK'ya göre anlaşmalı boşanma davası açabilmek için evliliğin en az ne kadar sürmüş olması gerekir?", "tmk_aile", "easy", ["TMK m.166"], ["anlaşmalı boşanma", "bir yıl", "ortak hayat"], "bir yıl", True, "TMK aile hukuku (YİM hazırlık - Faz 1 red bekleniyor)."),
        ("Mirasbırakanın tasarruf özgürlüğünün sınırı olan 'saklı pay' oranları altsoy için ne kadardır?", "tmk_genel", "hard", ["TMK m.506"], ["saklı pay", "altsoy", "yarısı", "tasarruf"], "yarısı", True, "TMK miras hukuku (YİM hazırlık).")
    ], 21)
]

data['questions'].extend(new_questions)

with open('/Users/btmacstudio/.openclaw/workspace/projects/hukuk-ai/configs/evaluation/test_questions.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print(f"Total questions written: {len(data['questions'])}")
