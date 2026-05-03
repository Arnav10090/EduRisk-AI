import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { UserPlus, FileSpreadsheet, BookOpen } from 'lucide-react';
import Link from 'next/link';

export function EmptyState() {
  return (
    <Card className="border-dashed">
      <CardContent className="flex flex-col items-center justify-center py-16 space-y-6">
        {/* Icon */}
        <div className="rounded-full bg-muted p-6">
          <FileSpreadsheet className="h-12 w-12 text-muted-foreground" />
        </div>

        {/* Message */}
        <div className="text-center space-y-2">
          <h3 className="text-2xl font-semibold">No students yet</h3>
          <p className="text-muted-foreground max-w-md">
            Get started by adding your first student to assess their placement risk 
            and receive AI-powered recommendations.
          </p>
        </div>

        {/* Call to Action */}
        <div className="flex gap-4">
          <Link href="/student/new">
            <Button size="lg" className="gap-2">
              <UserPlus className="h-5 w-5" />
              Add Your First Student
            </Button>
          </Link>
          
          <Link href="/docs">
            <Button size="lg" variant="outline" className="gap-2">
              <BookOpen className="h-5 w-5" />
              View API Documentation
            </Button>
          </Link>
        </div>
      </CardContent>
    </Card>
  );
}
