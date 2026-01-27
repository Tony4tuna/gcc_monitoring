from nicegui import ui

def main():
    ui.label('Work Order Form').classes('text-2xl font-bold text-primary mb-4')

    with ui.card().classes('w-full max-w-[1400px] mx-auto p-6 shadow-xl'):
        # ────────────────────────────────────────────────
        # CONTACT INFORMATION section
        # ────────────────────────────────────────────────
        ui.label('CONTACT INFORMATION').classes('text-xl font-semibold text-primary mb-3')

        with ui.row().classes('gap-6 w-full'):
            with ui.column().classes('flex-1 min-w-[280px]'):
                ui.label('Customer *').classes('font-medium')
                customer = ui.input(placeholder='Enter customer name').classes('w-full')

            with ui.column().classes('flex-1 min-w-[280px]'):
                ui.label('Location').classes('font-medium')
                location = ui.input(placeholder='Enter location').classes('w-full')

            with ui.column().classes('flex-1 min-w-[280px]'):
                ui.label('Equipment Unit').classes('font-medium')
                equipment = ui.input(placeholder='Enter equipment ID/unit').classes('w-full')

        ui.separator().classes('my-6')

        # ────────────────────────────────────────────────
        # SERVICE STATUS section
        # ────────────────────────────────────────────────
        ui.label('SERVICE STATUS').classes('text-xl font-semibold text-primary mb-3')

        with ui.row().classes('gap-8 w-full items-start'):
            # Status & Priority in smaller columns
            with ui.column().classes('flex-1 min-w-[220px]'):
                ui.label('Status').classes('font-medium')
                status = ui.select(
                    options=['Open', 'Closed', 'Pending', 'Completed'],
                    value='Open',
                    label='Select status'
                ).classes('w-full')

            with ui.column().classes('flex-1 min-w-[220px]'):
                ui.label('Priority').classes('font-medium')
                priority = ui.select(
                    options=['Normal', 'High', 'Emergency', 'Low'],
                    value='Normal',
                    label='Select priority'
                ).classes('w-full')

            # Work Order Title takes more space
            with ui.column().classes('flex-2 min-w-[400px]'):
                ui.label('Work Order Title *').classes('font-medium')
                title = ui.input(placeholder='Brief descriptive title').classes('w-full')

        ui.separator().classes('my-6')

        # ────────────────────────────────────────────────
        # Description fields – wide text areas
        # ────────────────────────────────────────────────
        ui.label('GENERAL DESCRIPTION [TECH TO FILL]').classes('font-medium text-lg mb-2')
        general_desc = ui.textarea(
            placeholder='Enter general description here...',
        ).classes('w-full min-h-[140px] text-base')

        ui.separator().classes('my-5')

        with ui.row().classes('gap-6 w-full'):
            with ui.column().classes('flex-1'):
                ui.label('MATERIALS & SERVICES [TECH TO FILL]').classes('font-medium text-lg mb-2')
                materials = ui.textarea(
                    placeholder='List materials and services used...',
                ).classes('w-full min-h-[180px]')

            with ui.column().classes('flex-1'):
                ui.label('LABOR DESCRIPTION [TECH TO FILL]').classes('font-medium text-lg mb-2')
                labor = ui.textarea(
                    placeholder='Describe labor performed...',
                ).classes('w-full min-h-[180px]')

        ui.separator().classes('my-6')

        # Action buttons
        with ui.row().classes('justify-end gap-4 mt-4'):
            ui.button('Cancel', color='grey').props('outline flat')
            ui.button('Save Draft', color='secondary')
            ui.button('Submit / Complete', color='primary').props('unelevated')

    # Make the whole page responsive and centered
    ui.context.client.request.headers['viewport'] = 'width=device-width, initial-scale=1'

ui.run(
    title='Work Order Entry – Wide Layout',
    host='0.0.0.0',
    port=8080,
    dark=None,          # None = follow system, True = dark, False = light
    reload=True,        # auto-reload during development
)