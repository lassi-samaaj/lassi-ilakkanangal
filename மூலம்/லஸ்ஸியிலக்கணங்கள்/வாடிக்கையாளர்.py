import json
import os
import unicodedata
from warnings import warn

import semantic_version
from lark import Lark, Tree, Visitor
from lark.reconstruct import Reconstructor
from nuchabäl import chijun
from எண்ணிக்கை import சுருங்குறித்தொடர் as சு, உரைக்கு as உ, முறைமைகள்


def எண்ணெழுத்து(ஆ, கண்டிப்பான=True):
    if len(ஆ) != 1:
        if கண்டிப்பான:
            return all(எண்ணெழுத்து(இ, கண்டிப்பான) for இ in ஆ)
        else:
            return any(எண்ணெழுத்து(இ, கண்டிப்பான) for இ in ஆ)
    return unicodedata.category(ஆ) in ['Lu', 'Ll', 'Lt', 'Lm', 'Lo', 'Nl', 'Mn', 'Mc', 'Nd', 'Pc']


class _சட்டம்_பகுப்பாய்வி(Visitor):
    def __init__(self):
        self.தேவை = False

    def literal(self, ஆ):
        if எண்ணெழுத்து(ஆ.children[0], கண்டிப்பான=False):
            self.தேவை = True


class நிரல்மொழித்தகவல்கள்(object):
    _தனிப்பட்ட_விதிகள் = [
        "NAME", "DEC_NUMBER"
    ]

    def __init__(தன், கோப்புறை):
        தன்.கோப்புறை = கோப்புறை
        தன்._தகவல்கள், தன்._மொழிபெயர்ப்புகள் = தன்._தகவல்கள்_படி()

    @property
    def நிரல்மொழிகள்(தன்):
        return list(தன்._தகவல்கள்)

    def மொழிகள்(தன், நிரல்மொழி, பதிப்பு=None):
        பதிப்பு = தன்.பதிப்பு_கண்டறி(நிரல்மொழி, பதிப்பு)
        விதிகள் = தன்.விதிகள்(நிரல்மொழி, பதிப்பு)
        return set(மொ for விதி in விதிகள் for மொ in தன்._மொழிபெயர்ப்புகள்[நிரல்மொழி]['விதிகள்'][விதி]["பெயர்ப்பு"])

    def பதிப்புகள்(தன், நிரல்மொழி):
        if 'பதிப்பு' in தன்._தகவல்கள்[நிரல்மொழி]:
            பதிப்புகள் = sorted([semantic_version.Version.coerce(ப) for ப in தன்._தகவல்கள்[நிரல்மொழி]['பதிப்பு']])
            return [str(ப) for ப in பதிப்புகள்]

    def நீட்சி(தன், நிரல்மொழி, மொழி, பதிப்பு=None):
        if மொழி == தன்.தகவல்(நிரல்மொழி, 'மொழி', பதிப்பு=பதிப்பு):
            return தன்.தகவல்(நிரல்மொழி, 'நீட்சி', பதிப்பு=பதிப்பு)
        try:
            return தன்._மொழிபெயர்ப்புகள்[நிரல்மொழி]['நீட்சி'][மொழி]
        except KeyError:
            pass

    def பெயர்(தன், நிரல்மொழி, மொழி, பதிப்பு=None):
        if மொழி == தன்.தகவல்(நிரல்மொழி, 'மொழி', பதிப்பு=பதிப்பு):
            return தன்.தகவல்(நிரல்மொழி, 'பெயர்', பதிப்பு=பதிப்பு)
        try:
            return தன்._மொழிபெயர்ப்புகள்[நிரல்மொழி]['பெயர்'][மொழி]
        except KeyError:
            pass

    def விதிகள்(தன், நிரல்மொழி, பதிப்பு=None):
        பதிப்பு = தன்.பதிப்பு_கண்டறி(நிரல்மொழி, பதிப்பு)
        try:
            விதி_பதிப்புகள் = தன்._மொழிபெயர்ப்புகள்[நிரல்மொழி]['பதிப்புகள்']
        except KeyError:
            return list(தன்._மொழிபெயர்ப்புகள்[நிரல்மொழி]['விதிகள்'])

        if பதிப்பு:
            return விதி_பதிப்புகள்[பதிப்பு]
        return விதி_பதிப்புகள்['']

    def விதி_மொழிபெயர்ப்பு(தன், நிரல்மொழி, மொழி, விதி):
        விதி_தகவல்கள் = தன்._மொழிபெயர்ப்புகள்[நிரல்மொழி]['விதிகள்'][விதி]
        if மொழி == தன்.தகவல்(நிரல்மொழி, 'மொழி', பதிப்பு=None):
            return விதி
        try:
            return விதி_தகவல்கள்["பெயர்ப்பு"][மொழி]
        except KeyError:
            if 'தேவை' in விதி_தகவல்கள் and not விதி_தகவல்கள்['தேவை']:
                return விதி

    def இலக்கணம்_விதிகள்(தன், நிரல்மொழி, மொழி=None, எண்ணுரு=None, பதிப்பு=None):
        பதிப்பு = தன்.பதிப்பு_கண்டறி(நிரல்மொழி, பதிப்பு)
        மொழி = மொழி or தன்.தகவல்(நிரல்மொழி, 'மொழி', பதிப்பு=பதிப்பு)
        எண்ணுரு = தன்.எண்ணுரு_பெறு(நிரல்மொழி, மொழி, எண்ணுரு, பதிப்பு=பதிப்பு)

        நிறைவு = தன்.நிறைவு(நிரல்மொழி, மொழி, பதிப்பு)
        if நிறைவு < 1:
            try:
                மொழி_பெயர் = chijun.ruchabäl(மொழி)
            except ValueError:
                மொழி_பெயர் = மொழி
            warn(
                '\nஎச்சரிக்கை: {மொழி} ￿￿￿{நிரல்மொழி} மொழிபெயர்ப்பு முழுமையாக தயார் இல்லை ! ({சத} சதவிதம்)\n'.format(
                    மொழி=மொழி_பெயர்,
                    நிரல்மொழி=தன்.பெயர்(நிரல்மொழி, 'த') or நிரல்மொழி,
                    சத=உ(round(நிறைவு, 3) * 100, 'தமிழ்')
                ))

        விதிகள் = தன்.விதிகள்(நிரல்மொழி, பதிப்பு=பதிப்பு)
        மாற்றப்பட்ட_விதிகள் = [தன்.விதி_மொழிபெயர்ப்பு(நிரல்மொழி, மொழி, வி) or வி for வி in விதிகள்]

        மாற்றப்பட்ட_விதிகள் += [
            'NAME: ID_START ID_CONTINUE*',
            'ID_START: /[\\p{Lu}\\p{Ll}\\p{Lt}\\p{Lm}\\p{Lo}\\p{Nl}_·]+/',
            'ID_CONTINUE: ID_START | /[\\p{Mn}\\p{Mc}\\p{Nd}\\p{Pc}]+/',
            f'DEC_NUMBER: /{சு(எண்ணுரு)}/'
        ]
        return மாற்றப்பட்ட_விதிகள்

    def நிறைவு(தன், நிரல்மொழி, மொழி, பதிப்பு=None):
        பதிப்பு = தன்.பதிப்பு_கண்டறி(நிரல்மொழி, பதிப்பு)
        if மொழி == தன்.தகவல்(நிரல்மொழி, 'மொழி', பதிப்பு=பதிப்பு):
            return 1

        விதிகள் = தன்.விதிகள்(நிரல்மொழி, பதிப்பு=பதிப்பு)
        மொழிபெயர்ப்புகள் = [தன்.விதி_மொழிபெயர்ப்பு(நிரல்மொழி, மொழி=மொழி, விதி=விதி) for விதி in விதிகள்]

        return len([உரை for உரை in மொழிபெயர்ப்புகள் if உரை]) / len(விதிகள்)

    def தகவல்(தன், நிரல்மொழி, தகவல், பதிப்பு=None):
        பதிப்பு = தன்.பதிப்பு_கண்டறி(நிரல்மொழி, பதிப்பு)

        மொழி_தகவல்கள் = தன்._தகவல்கள்[நிரல்மொழி]
        try:
            return மொழி_தகவல்கள்['பதிப்பு'][பதிப்பு][தகவல்]
        except KeyError:
            try:
                return மொழி_தகவல்கள்[தகவல்]
            except KeyError:
                pass

    def பதிப்பு_கண்டறி(தன், நிரல்மொழி, பதிப்பு):
        பதிப்புகள் = தன்.பதிப்புகள்(நிரல்மொழி)
        if not பதிப்புகள்:
            return
        பதிப்புகள் = [semantic_version.Version(ப) for ப in பதிப்புகள்]

        if not பதிப்புகள்:
            return None
        if பதிப்பு is None:
            return str(பதிப்புகள்[-1])

        _பதிப்பு = semantic_version.Version.coerce(str(பதிப்பு))

        try:
            return next(str(ப) for ப in பதிப்புகள்[::-1] if semantic_version.SimpleSpec(f'<={_பதிப்பு}').match(ப))
        except StopIteration:
            return str(பதிப்புகள்[-1])

    def நீட்சி_மூலம்_மொழி(தன், கோப்பு):
        பெயர், நீட்சி = கோப்பு.split('.')
        try:
            பெயர், மொழி_நீட்சி = பெயர்.split('.')
            raise NotImplementedError
        except ValueError:
            மொழி_நீட்சி = None
        நிரல்மொழி = next((நிரல் for நிரல், மதி in தன்._தகவல்கள்.items() if மதி['நீட்சி'] == நீட்சி), None)

        if நிரல்மொழி:
            return பெயர், நிரல்மொழி, [தன்.தகவல்(நிரல்மொழி, 'மொழி')]
        try:
            நிரல்மொழி = next(
                நிரல் for நிரல், மதி in தன்._மொழிபெயர்ப்புகள்.items() for மொ, நீ in மதி["நீட்சி"].items() if
                நீ == நீட்சி
            )
            மொழி = [மொ for மொ, நீ in தன்._மொழிபெயர்ப்புகள்[நிரல்மொழி]['நீட்சி'].items() if நீ == நீட்சி]
            return பெயர், நிரல்மொழி, மொழி
        except StopIteration:
            pass

    def எண்ணுரு_பெறு(தன், நிரல்மொழி, மொழி, எண்ணுரு, பதிப்பு=None):
        if எண்ணுரு in முறைமைகள்:
            return எண்ணுரு
        try:
            return chijun.rajilanïk(எண்ணுரு or மொழி)
        except ValueError:
            return தன்.தகவல்(நிரல்மொழி, 'எண்ணுரு', பதிப்பு=பதிப்பு)

    def தொகுத்தல்(தன்):
        லார்க்_இலக்கணம் = '\n'.join(தன்.விதிகள்('lark'))
        லார்க்_பகுப்பாய்வி = Lark(லார்க்_இலக்கணம்)
        புனரமைப்பு = Reconstructor(லார்க்_பகுப்பாய்வி)

        def _பின்_பகுப்பாயுவி(உரை):
            for ஈ in உரை:
                yield '{} '.format(ஈ) if len(ஈ.strip()) and not ஈ.strip(' \t').endswith('\n') else ஈ

        மொழிபெயர்ப்பு_அகராதிகள் = {}
        for நிரல்மொழி in தன்.நிரல்மொழிகள்:
            பதிப்புகள் = தன்.பதிப்புகள்(நிரல்மொழி) or ['']
            மொழிபெயர்ப்பு_அகராதி = {
                'நீட்சி': {},
                'பெயர்': {},
                'பதிப்புகள்': {ப: [] for ப in பதிப்புகள்},
                'விதிகள்': {},
                'மொழிபெயர்ப்பாளர்கள்': []
            }
            மொழிபெயர்ப்பு_அகராதிகள்[நிரல்மொழி] = மொழிபெயர்ப்பு_அகராதி

            for ப in பதிப்புகள்:
                இலக்கணம் = தன்._இலக்கணம்_உரை_பெற(நிரல்மொழி, பதிப்பு=ப)
                மரம் = லார்க்_பகுப்பாய்வி.parse(இலக்கணம்)

                for இ in மரம்.children:
                    if isinstance(இ, Tree):
                        if இ.children[0] in தன்._தனிப்பட்ட_விதிகள்:
                            continue
                        விதி = புனரமைப்பு.reconstruct(இ, postproc=_பின்_பகுப்பாயுவி).strip()
                        மொழிபெயர்ப்பு_அகராதி['பதிப்புகள்'][ப].append(விதி)

                        if விதி not in மொழிபெயர்ப்பு_அகராதி['விதிகள்']:
                            அகராதி = {'பெயர்ப்பு': {}}
                            பகுப்பாய்வி = _சட்டம்_பகுப்பாய்வி()
                            if இ.data in ['rule', 'token']:
                                பகுப்பாய்வி.visit(இ.children[1])
                                if not பகுப்பாய்வி.தேவை:
                                    அகராதி['தேவை'] = False
                            else:
                                அகராதி['தேவை'] = False
                            மொழிபெயர்ப்பு_அகராதி['விதிகள்'][விதி] = அகராதி

            try:
                முன் = தன்._மொழிபெயர்ப்புகள்[நிரல்மொழி]
            except KeyError:
                முன் = {'விதிகள்': {}}

            தன்._புதுப்பிப்பு(முன், மொழிபெயர்ப்பு_அகராதி)

            மொழிப்பெயர்_கோப்பு = f"{தன்.கோப்புறை}/{நிரல்மொழி}/மொழிபெயர்ப்புகள்.json"
            with open(மொழிப்பெயர்_கோப்பு, 'w', encoding='utf8') as கோ:
                json.dump(மொழிபெயர்ப்பு_அகராதி, கோ, ensure_ascii=False, indent=2)

    def சோதனைகள்(தன், நிரல்மொழி):
        சோதனைகள் = {}
        கோப்புரை = f'{தன்.கோப்புறை}/{நிரல்மொழி}/சோதனைகள்'
        if os.path.isdir(கோப்புரை):
            for கோப்பு in os.listdir(கோப்புரை):
                if os.path.isfile(f'{கோப்புரை}/{கோப்பு}'):
                    with open(f'{கோப்புரை}/{கோப்பு}', 'r', encoding='utf8') as கோ:
                        சோதனைகள்[கோப்பு] = ''.join(கோ.readlines())
        return சோதனைகள்

    def _தகவல்கள்_படி(தன்):
        தகவல்_அகராதி = {}
        மொழிபெயர்ப்பு_அகராதி = {}

        for கோப்புறை in os.listdir(தன்.கோப்புறை):
            முழு_முகவரி = f'{தன்.கோப்புறை}/{கோப்புறை}'
            தகவல்_முகவரி = f'{முழு_முகவரி}/தகவல்கள்.json'
            மொழிபெயர்ப்பு_முகவரி = f'{முழு_முகவரி}/மொழிபெயர்ப்புகள்.json'

            if os.path.isdir(முழு_முகவரி) and os.path.isfile(தகவல்_முகவரி):
                with open(தகவல்_முகவரி, mode='r', encoding='utf8') as கோ:
                    தகவல்கள் = json.load(கோ)
                    மொழி_பெயர் = தகவல்கள்['பெயர்']
                    தகவல்_அகராதி[மொழி_பெயர்] = தகவல்கள்

                if os.path.isfile(மொழிபெயர்ப்பு_முகவரி):
                    with open(மொழிபெயர்ப்பு_முகவரி, mode='r', encoding='utf8') as கோ:
                        மொழிபெயர்ப்புகள் = json.load(கோ)
                        மொழிபெயர்ப்பு_அகராதி[மொழி_பெயர்] = மொழிபெயர்ப்புகள்

        return தகவல்_அகராதி, மொழிபெயர்ப்பு_அகராதி

    def _இலக்கணம்_உரை_பெற(தன், நிரல்மொழி, பதிப்பு):
        கோப்பு = f'{தன்.கோப்புறை}/{நிரல்மொழி}/{தன்.தகவல்(நிரல்மொழி, "இலக்கணம்", பதிப்பு=பதிப்பு)}'
        with open(கோப்பு, encoding='utf8', mode='r') as கோ:
            return கோ.read()

    def _புதுப்பிப்பு(தன், முன், புதுச):
        for சாபி, ம in புதுச.items():
            if சாபி == "பதிப்புகள்":
                continue
            elif சாபி == "விதிகள்":
                for விதி in புதுச[சாபி]:
                    புதுச[சாபி][விதி].update(முன்[சாபி].get(விதி, {}))
            elif சாபி in முன்:
                புதுச[சாபி] = முன்[சாபி]
        return புதுச


நிரல்மொழிகள் = நிரல்மொழித்தகவல்கள்(f'{os.path.split(__file__)[0]}/இலக்கணங்கள்')
