"""Django management command to calculate and store divergences."""

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from apps.datafeeds.models import Symbol, Divergence
from apps.datafeeds.divergence_detector import DivergenceDetector


class Command(BaseCommand):
    help = 'Calculate and store divergences for all symbols and timeframes'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--symbol',
            type=str,
            help='Calculate divergences for specific symbol only',
        )
        parser.add_argument(
            '--timeframe',
            type=str,
            choices=['5m', '1h', '4h'],
            help='Calculate divergences for specific timeframe only',
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing divergences before calculating new ones',
        )
    
    def handle(self, *args, **options):
        self.stdout.write('Starting divergence calculation...')
        
        # Get symbols to process
        if options['symbol']:
            try:
                symbols = [Symbol.objects.get(code=options['symbol'])]
            except Symbol.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'Symbol {options["symbol"]} not found')
                )
                return
        else:
            symbols = Symbol.objects.filter(is_active=True)
        
        # Get timeframes to process
        if options['timeframe']:
            timeframes = [options['timeframe']]
        else:
            timeframes = ['5m', '1h', '4h']
        
        # Clear existing divergences if requested
        if options['clear']:
            self.stdout.write('Clearing existing divergences...')
            Divergence.objects.all().delete()
        
        # Initialize detector
        detector = DivergenceDetector()
        
        total_divergences = 0
        
        for symbol in symbols:
            self.stdout.write(f'Processing {symbol.code}...')
            
            for timeframe in timeframes:
                self.stdout.write(f'  Calculating {timeframe} divergences...')
                
                try:
                    # Detect divergences
                    divergences = detector.detect_all_divergences(symbol, timeframe)
                    
                    if divergences:
                        # Save divergences in bulk
                        with transaction.atomic():
                            Divergence.objects.bulk_create(divergences, ignore_conflicts=True)
                        
                        self.stdout.write(
                            f'    Found {len(divergences)} divergences'
                        )
                        total_divergences += len(divergences)
                    else:
                        self.stdout.write('    No divergences found')
                        
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(
                            f'    Error processing {symbol.code} {timeframe}: {str(e)}'
                        )
                    )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Divergence calculation completed. Total divergences: {total_divergences}'
            )
        )


