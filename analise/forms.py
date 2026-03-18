from django import forms

INDICATOR_CHOICES = [
    ("Children (0-14) living with HIV", "Children (0-14) living with HIV"),
    ("Adults (ages 15-49) newly infected with HIV", "Adults (ages 15-49) newly infected with HIV"),
    ("Young people (ages 15-24) newly infected with HIV", "Young people (ages 15-24) newly infected with HIV"),
    ("Women's share of population ages 15+ living with HIV (%)", "Women's share of population ages 15+ living with HIV (%)"),
    ("Incidence of HIV, ages 15-24 (per 1,000 uninfected population ages 15-24)", "Incidence of HIV, ages 15-24 (per 1,000 uninfected population ages 15-24)"),
    ("Children (ages 0-14) newly infected with HIV", "Children (ages 0-14) newly infected with HIV"),
    ("Prevalence of HIV, female (% ages 15-24)", "Prevalence of HIV, female (% ages 15-24)"),
    ("Incidence of HIV, ages 15-49 (per 1,000 uninfected population ages 15-49)", "Incidence of HIV, ages 15-49 (per 1,000 uninfected population ages 15-49)"),
    ("Adults (ages 15+) and children (ages 0-14) newly infected with HIV", "Adults (ages 15+) and children (ages 0-14) newly infected with HIV"),
    ("Prevalence of HIV, total (% of population ages 15-49)", "Prevalence of HIV, total (% of population ages 15-49)"),
    ("Prevalence of HIV, male (% ages 15-24)", "Prevalence of HIV, male (% ages 15-24)"),
    ("Prevalence of HIV", "Prevalence of HIV"),
    ("Incidence of HIV, all (per 1,000 uninfected population)", "Incidence of HIV, all (per 1,000 uninfected population)"),
]

class IndicatorForm(forms.Form):
    indicator = forms.ChoiceField(choices=INDICATOR_CHOICES, label="Escolha um indicador")
