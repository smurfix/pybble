#!/usr/bin/perl

my $BP;

BEGIN {
	$/ = undef;
	open(BP,"_boilerplate.py") or die "no boilerplate file found\n";
	$BP = <BP>;
	close(BP);
	$BP =~ s:\n+\z:\n##BP\n\n:;

	$/ = "";
}

while(<ARGV>) {
	print $1 if s:\A(#!/.+\n):: ;
	$_ = $BP if m:^##\s*BP\s*\n+\z:m;
	print;
}