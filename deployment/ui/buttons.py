from nicegui import ui

ui.label('Quasar → NiceGUI Button Examples (ALL)').classes('text-h4 q-mb-md')

# =========================================================
# 1) TEXT BUTTONS
# =========================================================
ui.label('1) Text Buttons').classes('text-h6 q-mt-md')
with ui.row().classes('q-pa-md q-gutter-sm'):
    ui.button('Standard', color='white').props('text-color=black')
    ui.button('Primary', color='primary')
    ui.button('Secondary', color='secondary')
    ui.button('Amber', color='amber').props('glossy')
    ui.button('Brown 5', color='brown-5')
    ui.button('Deep Orange', color='deep-orange').props('glossy')
    ui.button('Purple', color='purple')
    ui.button('Black', color='black')

ui.separator().classes('q-my-md')

# =========================================================
# 2) SQUARE ICON BUTTONS
# =========================================================
ui.label('2) Square Icon Buttons').classes('text-h6 q-mt-md')
with ui.row().classes('q-pa-md q-gutter-sm'):
    ui.button(icon='shopping_cart', color='primary').props('square')
    ui.button(icon='navigation', color='secondary').props('square')
    ui.button(icon='layers_clear', color='amber').props('square glossy text-color=black')
    ui.button(icon='directions', color='brown-5').props('square')
    ui.button(icon='edit_location', color='deep-orange').props('square')
    ui.button(icon='local_grocery_store', color='purple').props('square glossy')
    ui.button(icon='my_location', color='black').props('square')

ui.separator().classes('q-my-md')

# =========================================================
# 3) ICON LEFT / RIGHT / BOTH + STACKED
# =========================================================
ui.label('3) Icon Position + Stacked').classes('text-h6 q-mt-md')
with ui.row().classes('q-pa-md q-gutter-sm'):
    ui.button('On Left', icon='mail', color='primary')
    ui.button('On Right', color='secondary').props('icon-right=mail')
    ui.button('On Left and Right', icon='mail', color='red').props('icon-right=send')

with ui.row().classes('q-pa-md q-gutter-sm'):
    ui.button('Stacked', icon='phone', color='purple').props('stack glossy')

ui.separator().classes('q-my-md')

# =========================================================
# 4) ADVANCED / CUSTOM CONTENT BUTTONS
# =========================================================
ui.label('4) Advanced / Custom Content').classes('text-h6 q-mt-md')
with ui.row().classes('q-pa-md q-gutter-md'):

    # 4.1 Button with big icon + label
    with ui.button(color='teal'):
        ui.icon('map').classes('q-mr-sm').style('font-size: 3em')
        ui.label('Label')

    # 4.2 Round button with avatar image
    with ui.button().props('round'):
        with ui.avatar(size='42px'):
            ui.image('https://cdn.quasar.dev/img/avatar2.jpg')

    # 4.3 Multiline button, no caps
    with ui.button(color='indigo').props('no-caps'):
        ui.html('Multiline<br>Button')

    # 4.4 Push button with custom inner layout
    with ui.button(color='deep-orange').props('push'):
        with ui.row().classes('items-center no-wrap'):
            ui.icon('map').classes('q-mr-sm')
            with ui.column().classes('text-center'):
                ui.html('Custom<br>Content')

# Run on a different port than your main app to avoid conflicts
ui.run(host='127.0.0.1', port=8088, title='Buttons Demo (ALL)')
